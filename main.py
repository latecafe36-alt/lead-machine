import os
import psycopg2
import requests
from bs4 import BeautifulSoup
import time

# =========================
# CONFIG
# =========================
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("❌ DATABASE_URL manquante !")

print("✅ Variables OK")

# =========================
# DB CONNECTION
# =========================
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    name TEXT,
    title TEXT,
    link TEXT UNIQUE,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

# =========================
# SCRAPER (Google Search hack)
# =========================
QUERY = 'site:linkedin.com/in "CEO" "SaaS" "Paris" OR "Genève" "looking for investors"'

def scrape_google():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    url = f"https://www.google.com/search?q={QUERY}&num=10"
    res = requests.get(url, headers=headers)

    soup = BeautifulSoup(res.text, "html.parser")

    results = []

    for g in soup.select("div.g"):
        link_tag = g.find("a")
        title = g.find("h3")

        if link_tag and title:
            link = link_tag["href"]
            name = title.text

            results.append({
                "name": name,
                "title": "CEO / Founder",
                "link": link
            })

    return results

# =========================
# SAVE TO DB
# =========================
def save_leads(leads):
    for lead in leads:
        try:
            cur.execute("""
                INSERT INTO leads (name, title, link)
                VALUES (%s, %s, %s)
                ON CONFLICT (link) DO NOTHING
            """, (lead["name"], lead["title"], lead["link"]))

        except Exception as e:
            print("Erreur insertion:", e)

    conn.commit()

# =========================
# LOOP
# =========================
while True:
    print("🚀 Scraping...")
    leads = scrape_google()
    print(f"✅ {len(leads)} leads trouvés")

    save_leads(leads)

    print("💾 Sauvegardé en DB")
    time.sleep(300)
