import os
import psycopg2
import requests

DATABASE_URL = os.getenv("DATABASE_URL")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

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

def scrape_linkedin():
    url = "https://serpapi.com/search"

    queries = [
        'site:linkedin.com/in "CEO" "startup" "Paris"',
        'site:linkedin.com/in "Founder" "SaaS" "Geneva"',
        'site:linkedin.com/in "co-founder" "AI startup"',
    ]

    leads = []

    for q in queries:
        params = {
            "engine": "google",
            "q": q,
            "api_key": SERPAPI_KEY,
            "num": 20
        }

        res = requests.get(url, params=params)
        data = res.json()

        for result in data.get("organic_results", []):
            link = result.get("link")
            title = result.get("title")

            if link and "linkedin.com/in" in link:
                leads.append({
                    "name": title,
                    "title": title,
                    "linkedin": link
                })

    return leads


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


if __name__ == "__main__":
    print("🚀 Scraping...")
    leads = scrape_linkedin()

    print(f"Found {len(leads)} leads")

    save_leads(leads)

    print("✅ Done")
