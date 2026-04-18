import os
import requests
import psycopg2

# ===== CONFIG =====
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

if not SERPAPI_KEY:
    raise Exception("❌ SERPAPI_KEY manquante !")

if not DATABASE_URL:
    raise Exception("❌ DATABASE_URL manquante !")

print("✅ Variables OK")

# ===== DB CONNECTION =====
conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cur = conn.cursor()

print("✅ Connecté à la DB")

# ===== CREATE TABLE =====
cur.execute("""
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    title TEXT,
    link TEXT UNIQUE
)
""")
conn.commit()

print("✅ Table prête")

# ===== SERPAPI REQUEST =====
params = {
    "engine": "google",
    "q": 'site:linkedin.com/in "CEO" "SaaS" "Paris" OR "Genève" "looking for investors"',
    "api_key": SERPAPI_KEY
}

print("🚀 Lancement scraping...")

response = requests.get("https://serpapi.com/search", params=params)
data = response.json()

results = data.get("organic_results", [])

print(f"👉 {len(results)} résultats trouvés")

# ===== SAVE TO DB =====
for r in results:
    title = r.get("title")
    link = r.get("link")

    try:
        cur.execute(
            "INSERT INTO leads (title, link) VALUES (%s, %s) ON CONFLICT (link) DO NOTHING",
            (title, link)
        )
        conn.commit()
        print(f"✅ Saved: {title}")

    except Exception as e:
        print("❌ Erreur insertion:", e)

# ===== CLEAN =====
cur.close()
conn.close()

print("🎉 Terminé !")
