import requests
import pandas as pd
from datetime import datetime
import os
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

MAX_THREADS = 5

# 🔥 QUERIES INSTAGRAM
queries = [
    'site:instagram.com "founder startup"',
    'site:instagram.com "ceo startup"',
    'site:instagram.com "ai startup"',
    'site:instagram.com "entrepreneur startup"',
    'site:instagram.com "saas founder"',
]

# -------- SAFE REQUEST --------
def safe_request(url, params, retries=3):
    for _ in range(retries):
        try:
            return requests.get(url, params=params, timeout=10).json()
        except:
            time.sleep(random.randint(1, 3))
    return {}

# -------- SCORE --------
def score_lead(snippet, name):
    text = (snippet or "").lower()
    score = 0

    for k in ["startup", "ai", "saas", "founder", "ceo"]:
        if k in text:
            score += 1

    return score

# -------- PROCESS --------
def process_lead(r):
    link = r.get("link", "")
    title = r.get("title", "")
    snippet = r.get("snippet", "")

    if "instagram.com" not in link:
        return None

    if "/p/" in link or "/reel/" in link:
        return None  # skip posts

    score = score_lead(snippet, title)

    if score < 2:
        return None

    return {
        "name": title,
        "instagram": link,
        "bio": snippet,
        "score": score,
        "date": datetime.today().strftime('%Y-%m-%d')
    }

# -------- SCRAPE --------
def scrape():
    results = []

    for query in queries:
        print(f"\n🔎 Query: {query}")

        params = {
            "q": query,
            "num": 50,
            "api_key": SERPAPI_KEY,
            "google_domain": "google.com",
            "hl": "en",
            "gl": "us"
        }

        data = safe_request("https://serpapi.com/search", params)
        leads = data.get("organic_results", [])

        print(f"👉 {len(leads)} résultats")

        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(process_lead, r) for r in leads]

            for future in as_completed(futures):
                lead = future.result()
                if not lead:
                    continue

                print(f"👤 {lead['name']}")
                results.append(lead)

    df = pd.DataFrame(results)

    if not df.empty:
        df = df.drop_duplicates(subset=["instagram"])

    print(f"\n✅ {len(df)} leads uniques")
    return df

# -------- SAVE --------
def save(df):
    if df.empty:
        print("⚠️ Aucun lead")
        return

    if os.path.exists("insta_leads.csv"):
        df.to_csv("insta_leads.csv", mode="a", header=False, index=False)
    else:
        df.to_csv("insta_leads.csv", index=False)

    print("💾 insta_leads.csv sauvegardé")

# -------- LOOP --------
if __name__ == "__main__":
    print("🚀 Machine Instagram lancée...")

    while True:
        df = scrape()
        save(df)

        print("⏸️ Pause 1h...\n")
        time.sleep(3600)
