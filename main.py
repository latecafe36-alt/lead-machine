import os
import psycopg2
import requests

# =====================
# CONFIG
# =====================
DATABASE_URL = os.getenv("DATABASE_URL")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# =====================
# DB CONNECTION
# =====================
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# =====================
# CREATE TABLE
# =====================
cur.execute("""
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    name TEXT,
    title TEXT,
    linkedin_url TEXT UNIQUE,
    email TEXT
);
""")
conn.commit()

# =====================
# SCRAPER GOOGLE (LinkedIn)
# =====================
def scrape_linkedin():
    url = "https://serpapi.com/search"
    
    params = {
        "engine": "google",
        "q": 'site:linkedin.com/in "CEO" "SaaS" ("Paris" OR "Geneva") "looking for investors"',
        "api_key": SERPAPI_KEY
    }

    res = requests.get(url, params=params)
    data = res.json()

    leads = []

    for result in data.get("organic_results", []):
        title = result.get("title")
        link = result.get("link")

        if "linkedin.com/in" in link:
            leads.append({
                "name": title,
                "title": title,
                "linkedin": link
            })

    return leads

# =====================
# SAVE TO DB
# =====================
def save_leads(leads):
    for lead in leads:
        try:
            cur.execute("""
                INSERT INTO leads (name, title, linkedin_url)
                VALUES (%s, %s, %s)
                ON CONFLICT (linkedin_url) DO NOTHING
            """, (lead["name"], lead["title"], lead["linkedin"]))
        except Exception as e:
            print("Error:", e)

    conn.commit()

# =====================
# MAIN
# =====================
if __name__ == "__main__":
    print("🚀 Scraping...")
    leads = scrape_linkedin()

    print(f"Found {len(leads)} leads")

    save_leads(leads)

    print("✅ Done")
