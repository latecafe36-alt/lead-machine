import os
import psycopg2
import requests

DATABASE_URL = os.getenv("DATABASE_URL")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Table
cur.execute("""
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    name TEXT,
    title TEXT,
    linkedin_url TEXT UNIQUE,
    country TEXT,
    keyword TEXT
);
""")
conn.commit()


def scrape_linkedin():
    url = "https://serpapi.com/search"

    queries = [
        # 🇨🇭 Suisse
        ('site:linkedin.com/in ("Founder" OR "CEO") ("startup" OR "SaaS") "Switzerland" "raising"', "Switzerland", "raising"),
        ('site:linkedin.com/in ("Founder" OR "CEO") "AI startup" "Switzerland" "hiring"', "Switzerland", "hiring"),

        # 🇵🇹 Portugal
        ('site:linkedin.com/in ("Founder" OR "CEO") ("startup" OR "SaaS") "Portugal" "funding"', "Portugal", "funding"),
        ('site:linkedin.com/in ("Founder" OR "CEO") "startup" "Portugal" "hiring"', "Portugal", "hiring"),

        # 🇧🇪 Belgique
        ('site:linkedin.com/in ("Founder" OR "CEO") ("startup" OR "SaaS") "Belgium" "raising"', "Belgium", "raising"),
        ('site:linkedin.com/in ("Founder" OR "CEO") "startup" "Brussels" "hiring"', "Belgium", "hiring"),

        # 🇬🇧 UK
        ('site:linkedin.com/in ("Founder" OR "CEO") ("startup" OR "SaaS") "United Kingdom" "raising"', "UK", "raising"),
        ('site:linkedin.com/in ("Founder" OR "CEO") "startup" "London" "seed"', "UK", "seed"),
    ]

    leads = []

    for q, country, keyword in queries:
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
                    "linkedin": link,
                    "country": country,
                    "keyword": keyword
                })

    return leads


def save_leads(leads):
    for lead in leads:
        try:
            cur.execute("""
                INSERT INTO leads (name, title, linkedin_url, country, keyword)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (linkedin_url) DO NOTHING
            """, (
                lead["name"],
                lead["title"],
                lead["linkedin"],
                lead["country"],
                lead["keyword"]
            ))
        except Exception as e:
            print("Error:", e)

    conn.commit()


if __name__ == "__main__":
    print("🚀 Scraping hot leads...")

    leads = scrape_linkedin()

    print(f"🔥 Found {len(leads)} leads")

    save_leads(leads)

    print("✅ Done")
