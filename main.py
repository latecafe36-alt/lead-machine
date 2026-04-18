import requests
import pandas as pd
from datetime import datetime
import os
import time
import random

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# 🔥 QUERIES QUI DONNENT DES RÉSULTATS
queries = [
    "AI startup hiring",
    "SaaS startup hiring",
    "machine learning startup hiring",
    "tech startup hiring Europe",
    "startup hiring engineer"
]

# -------- SAFE REQUEST --------
def safe_request(params, retries=3):
    for _ in range(retries):
        try:
            res = requests.get("https://serpapi.com/search", params=params, timeout=15)
            return res.json()
        except Exception as e:
            print("⚠️ Request error:", e)
            time.sleep(random.randint(1, 3))
    return {}

# -------- SCRAPE JOBS --------
def scrape_jobs():
    results = []

    for query in queries:
        print(f"\n🔎 Query: {query}")

        params = {
            "engine": "google_jobs",
            "q": query,
            "api_key": SERPAPI_KEY
        }

        data = safe_request(params)

        jobs = data.get("jobs_results", [])

        print(f"👉 {len(jobs)} jobs trouvés")

        for job in jobs:
            company = job.get("company_name", "")
            title = job.get("title", "")
            location = job.get("location", "")
            via = job.get("via", "")

            if not company:
                continue

            print(f"🏢 {company} | {title}")

            results.append({
                "company": company,
                "job_title": title,
                "location": location,
                "source": via,
                "date": datetime.today().strftime('%Y-%m-%d')
            })

    df = pd.DataFrame(results)

    if not df.empty:
        df = df.drop_duplicates(subset=["company"])

    print(f"\n✅ {len(df)} entreprises uniques")
    return df

# -------- SAVE --------
def save(df):
    if df.empty:
        print("⚠️ Aucun lead")
        return

    if os.path.exists("companies.csv"):
        df.to_csv("companies.csv", mode="a", header=False, index=False)
    else:
        df.to_csv("companies.csv", index=False)

    print("💾 companies.csv sauvegardé")

# -------- LOOP --------
if __name__ == "__main__":
    print("🚀 Machine lead gen lancée (jobs)...")

    while True:
        try:
            df = scrape_jobs()
            save(df)

            print("⏸️ Pause 1h...\n")
            time.sleep(3600)

        except Exception as e:
            print("💥 Crash:", e)
            time.sleep(60)
