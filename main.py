import os
import requests
import psycopg2

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

countries = [
    "Switzerland",
    "Portugal",
    "Belgium",
    "United Kingdom"
]

keywords = [
    "CEO SaaS",
    "Founder startup",
    "looking for investors",
    "raising funds"
]

def get_google_results(query):
    url = "https://serpapi.com/search"
    
    params = {
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": 20
    }
    
    res = requests.get(url, params=params)
    data = res.json()
    
    results = []
    
    for r in data.get("organic_results", []):
        link = r.get("link", "")
        title = r.get("title", "")
        
        if "linkedin.com/in/" in link:
            results.append({
                "name": title,
                "link": link
            })
    
    return results


def save_to_db(leads):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id SERIAL PRIMARY KEY,
            name TEXT,
            link TEXT UNIQUE
        )
    """)
    
    for lead in leads:
        try:
            cur.execute(
                "INSERT INTO leads (name, link) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (lead["name"], lead["link"])
            )
        except:
            pass
    
    conn.commit()
    cur.close()
    conn.close()


def main():
    print("🚀 Scraping hot leads...")

    all_leads = []

    for country in countries:
        for keyword in keywords:
            
            query = f'site:linkedin.com/in "{keyword}" "{country}"'
            
            print(f"🔍 {query}")
            
            leads = get_google_results(query)
            all_leads.extend(leads)

    print(f"🔥 Found {len(all_leads)} leads")

    if all_leads:
        save_to_db(all_leads)
        print("✅ Saved to DB")
    else:
        print("❌ No leads found")


if __name__ == "__main__":
    main()
