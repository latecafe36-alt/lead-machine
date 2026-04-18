import requests
import pandas as pd
from datetime import datetime
import os
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

MAX_THREADS = 5

# 🔥 QUERIES OPTIMISÉES (SANS GUILLEMETS)
queries = [
    'site:linkedin.com/in founder startup',
    'site:linkedin.com/in ceo startup',
    'site:linkedin.com/in ai startup founder',
    'site:linkedin.com/in saas founder',
    'site:linkedin.com/in entrepreneur startup',
]

# 🌍 PAYS CIBLÉS
TARGET_COUNTRIES = ["switzerland", "germany", "belgium", "portugal"]

# -------- SAFE REQUEST --------
def safe_request(url, params, retries=3):
    for _ in range(retries):
        try:
            return requests.get(url, params=params, timeout=10).json()
        except Exception as e:
            print(f"⚠️ Erreur requête: {e}")
            time.sleep(random.randint(1, 3))
    return {}

# -------- SCORE --------
def score_lead(snippet, name):
    text = (snippet or "").lower()
    score = 0

    for k in ["ai", "machine learning", "startup", "saas"]:
        if k in text:
            score += 1

    if "founder" in name.lower() or "ceo" in name.lower():
        score += 2

    return score

# -------- FILTRE PAYS --------
def is_target_country(snippet):
    text = (snippet or "").lower()
    return any(c in text for c in TARGET_COUNTRIES)

# -------- PROCESS LEAD --------
def process_lead(r):
    link = r.get("link", "")
    name = r.get("title", "")
    snippet = r.get("snippet", "")

    if not link or "linkedin.com/in" not in link:
        return None

    if not is_target_country(snippet):
        return None

    score = score_lead(snippet, name)

    if score < 2:
        return None

    return {
        "name": name,
        "linkedin": link,
        "snippet": snippet,
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

        print(f"👉 {len(leads)} résultats trouvés")

        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(process_lead, r) for r in leads]

            for future in as_completed(futures):
                lead = future.result()
                if not lead:
                    continue

                print(f"👤 {lead['name']} | score: {lead['score']}")
                results.append(lead)

    print(f"\n💾 {len(results)} leads avant déduplication")

    # 🔥 SUPPRESSION DOUBLONS
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.drop_duplicates(subset=["linkedin"])

    print(f"✅ {len(df)} leads uniques")
    return df

# -------- SAVE --------
def save(df):
    if df.empty:
        print("⚠️ Aucun lead à sauvegarder")
        return

    if os.path.exists("leads.csv"):
        df.to_csv("leads.csv", mode="a", header=False, index=False)
    else:
        df.to_csv("leads.csv", index=False)

    print("💾 leads.csv mis à jour")

# -------- RUN LOOP --------
if __name__ == "__main__":
    print("🚀 Machine scraping lancée...")

    while True:
        df = scrape()
        save(df)

        print("⏸️ Pause 1h...\n")
        time.sleep(3600)
