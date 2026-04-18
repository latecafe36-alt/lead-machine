import requests
import csv
import time
from datetime import datetime

SERPAPI_KEY = "ad58d596173b2c3e38df2090c2e4f6b3a1c954d1acbdc841727d9d7d15e1adfb"

queries = [
    'site:linkedin.com/posts "raising funds" startup',
    'site:linkedin.com/posts "looking for investors" startup'
]

def extract_profile(url):
    try:
        return "https://www.linkedin.com/in/" + url.split("/posts/")[1].split("_")[0]
    except:
        return ""

def score(text):
    t = text.lower()
    s = 0
    if "raising" in t: s += 3
    if "investors" in t: s += 4
    return s

def run_scraper():
    leads = []

    for q in queries:
        for start in range(0, 20, 10):
            params = {
                "q": q,
                "api_key": SERPAPI_KEY,
                "start": start
            }

            res = requests.get("https://serpapi.com/search", params=params).json()

            for r in res.get("organic_results", []):
                link = r.get("link", "")
                snippet = r.get("snippet", "")

                if "linkedin.com/posts" not in link:
                    continue

                profile = extract_profile(link)
                s = score(snippet)

                leads.append({
                    "profile": profile,
                    "post": link,
                    "score": s,
                    "date": datetime.today().strftime('%Y-%m-%d')
                })

            time.sleep(1)

    save(leads)

def save(leads):
    with open("db.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["profile","post","score","date"])
        if f.tell() == 0:
            writer.writeheader()

        for l in leads:
            writer.writerow(l)
