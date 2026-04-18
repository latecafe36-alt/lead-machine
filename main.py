import os
import requests
import psycopg2

# ===== CONFIG =====
API_KEY = os.getenv("SERPAPI_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

if not API_KEY:
    raise Exception("❌ SERPAPI_KEY manquante !")

if not DATABASE_URL:
    raise Exception("❌ DATABASE_URL manquante !")

# ===== DB CONNECTION =====
conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    title TEXT,
    link TEXT UNIQUE
)
""")
conn.commit()

# ===== SAVE FUNCTION =====
def save_lead(title, link):
    try:
        cur.execute("""
            INSERT INTO leads (title, link)
            VALUES (%s, %s)
            ON CONFLICT (link) DO NOTHING
        """, (title, link))
        conn.commit()
        print(f"✅ Saved: {title}")
    except Exception as e:
        print("❌ DB ERROR:", e)

# ===== SEARCH QUERY =====
query = 'site:linkedin.com/in "CEO" "SaaS" ("Paris" OR "Genève")'

print("🚀 START SCRAPING...")
print("🔎 Query:", query)

# ===== LOOP PAGES =====
for start in range(0, 20, 10):
    params = {
        "engine": "google",
        "q": query,
        "api_key": API_KEY,
        "start": start,
        "num": 10
    }

    try:
        response = requests.get("https://serpapi.com/search", params=params)
        data = response.json()

        if "error" in data:
            print("❌ SERPAPI ERROR:", data["error"])
            continue

        results = data.get("organic_results", [])

        print(f"👉 {len(results)} résultats page {start}")

        for r in results:
            title = r.get("title")
            link = r.get("link")

            if not link:
                continue

            print("➡️", title)
            save_lead(title, link)

    except Exception as e:
        print("❌ REQUEST ERROR:", e)

cur.close()
conn.close()

print("✅ FINISHED")
