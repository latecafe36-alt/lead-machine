import os
import requests
import time
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
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("✅ Connexion DB OK")

# ===== CREATE TABLE =====
cur.execute("""
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    title TEXT,
    link TEXT UNIQUE,
    snippet TEXT,
    score INT,
    city TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
print("✅ Table prête")

# 🌍 VILLES CIBLÉES
cities = [
    "Zurich", "Geneva", "Lausanne", "Basel", "Bern", "Zug",
    "Lucerne", "St Gallen", "Winterthur",
    "Brussels", "Antwerp", "Ghent", "Liege",
    "Charleroi", "Namur", "Leuven"
]

# 🔎 QUERIES
base_queries = [
    '"raising funds" startup',
    '"looking for investors" startup',
    '"seed round" startup',
    '"pre-seed startup"',
    '"series A startup"',
    '"raising capital startup"',
    '"we are raising startup"',
    '"startup fundraising"',
    '"looking for VC startup"',
    '"angel investors startup"'
]

# 🧠 SCORING
def score(text):
    t = text.lower()
    s = 0

    keywords = {
        "raising": 3,
        "funding": 3,
        "investors": 4,
        "seed": 3,
        "series a": 4,
        "pre-seed": 3,
        "capital": 2,
        "vc": 3,
        "angel": 3
    }

    for k, v in keywords.items():
        if k in t:
            s += v

    return s

print("🚀 START SCRAPING...\n")

seen_links = set()
inserted = 0

# 🔁 LOOP
for city in cities:
    for base in base_queries:

        query = f'site:linkedin.com/posts {base} "{city}"'
        print(f"🔎 {query}")

        for start in range(0, 100, 10):

            params = {
                "engine": "google",
                "q": query,
                "api_key": SERPAPI_KEY,
                "start": start,
                "num": 10,
                "tbs": "qdr:d"
            }

            try:
                response = requests.get("https://serpapi.com/search", params=params)
                data = response.json()
                results = data.get("organic_results", [])

                print(f"👉 {len(results)} résultats (page {start//10 + 1})")

                for r in results:
                    link = r.get("link", "")
                    title = r.get("title", "")
                    snippet = r.get("snippet", "")

                    text = title + " " + snippet
                    s = score(text)

                    if link and link not in seen_links and s >= 5:
                        seen_links.add(link)

                        try:
                            cur.execute("""
                                INSERT INTO leads (title, link, snippet, score, city)
                                VALUES (%s, %s, %s, %s, %s)
                                ON CONFLICT (link) DO NOTHING
                            """, (title, link, snippet, s, city))

                            inserted += 1

                        except Exception as e:
                            print("❌ DB erreur :", e)

            except Exception as e:
                print("❌ API erreur :", e)

            time.sleep(1)

# ===== SAVE =====
conn.commit()

print(f"\n🔥 {inserted} leads insérés en DB")

# ===== CLEAN =====
cur.close()
conn.close()

print("🚀 FIN OK")
