import os
import requests
import psycopg2

# ========================
# CONFIG
# ========================

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# ========================
# DB CONNECTION
# ========================

def get_db():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id SERIAL PRIMARY KEY,
            title TEXT,
            link TEXT UNIQUE,
            snippet TEXT,
            city TEXT,
            score INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

# ========================
# SCORE
# ========================

def compute_score(title="", snippet=""):
    text = (title + " " + snippet).lower()
    score = 0

    if "ceo" in text:
        score += 5
    if "founder" in text:
        score += 5
    if "saas" in text:
        score += 3
    if "startup" in text:
        score += 3
    if "fund" in text:
        score += 5

    return score

# ========================
# GOOGLE SEARCH VIA SERPAPI
# ========================

def search_google(query):
    print(f"\n🔎 QUERY: {query}")

    url = "https://serpapi.com/search"

    params = {
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": 10
    }

    try:
        res = requests.get(url, params=params)
        data = res.json()

        if "error" in data:
            print("❌ SERPAPI ERROR:", data["error"])
            return []

        results = data.get("organic_results", [])
        print(f"➡️ {len(results)} résultats bruts")

    except Exception as e:
        print("❌ API crash:", e)
        return []

    leads = []

    for r in results:
        link = r.get("link", "")
        title = r.get("title", "")
        snippet = r.get("snippet", "")

        if "linkedin.com/in/" in link:
            score = compute_score(title, snippet)

            leads.append({
                "title": title,
                "link": link,
                "snippet": snippet,
                "city": None,
                "score": score
            })

    print(f"🔥 {len(leads)} leads LinkedIn trouvés")

    return leads

# ========================
# SAVE TO DB
# ========================

def save_leads(leads):
    if not leads:
        return

    conn = get_db()
    cur = conn.cursor()

    for lead in leads:
        try:
            cur.execute(
                """
                INSERT INTO leads (title, link, snippet, city, score)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (link) DO NOTHING
                """,
                (
                    lead["title"],
                    lead["link"],
                    lead["snippet"],
                    lead["city"],
                    lead["score"]
                )
            )
            print("✅ Inserted:", lead["link"])

        except Exception as e:
            print("❌ DB error:", e)

    conn.commit()
    cur.close()
    conn.close()

# ========================
# MAIN SCRAPER
# ========================

def run_scraper():
    print("🚀 Starting scraping...")

    queries = []

    keywords = [
        "CEO SaaS",
        "Founder startup",
        "looking for investors",
        "raising funds",
        "seed round startup",
        "Series A startup"
    ]

    countries = [
        "France",
        "Germany",
        "Netherlands",
        "Spain",
        "Switzerland",
        "Belgium",
        "Portugal",
        "United Kingdom",
        "Austria",
        "Brazil",
        "Kuwait"
    ]

    for country in countries:
        for keyword in keywords:
            q = f'site:linkedin.com/in "{keyword}" "{country}"'
            queries.append(q)

    total = 0

    for q in queries:
        leads = search_google(q)
        save_leads(leads)
        total += len(leads)

    print("\n======================")
    print(f"🔥 TOTAL LEADS: {total}")
    print("======================")

# ========================
# ENTRYPOINT
# ========================

if __name__ == "__main__":
    init_db()
    run_scraper()
