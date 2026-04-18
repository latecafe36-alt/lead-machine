import requests
import csv
import time
from datetime import datetime
from config import SERPAPI_KEY, MIN_SCORE

queries = [
    'site:linkedin.com/posts "raising funds" startup',
    'site:linkedin.com/posts "looking for investors" startup',
    'site:linkedin.com/posts "seed round" startup'
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
    if "seed" in t or "series a" in t: s += 3
    return s

def generate_msg(snippet):
    return f"""Hey,

I saw your post:
"{snippet[:100]}..."

Looks like you're raising.

Open to a quick chat?"""

def load_existing():
    try:
        with open("db.csv", "r", encoding="utf-8") as f:
            return set(row["profile"] for row in csv.DictReader(f))
    except:
        return set()

def save(leads):
    file_exists = False
    try:
        open("db.csv")
        file_exists = True
    except:
        pass

    with open("db.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["profile","post","score","message","date"])
        if not file_exists:
            writer.writeheader()

        for l in leads:
            writer.writerow(l)

def run():
    existing = load_existing()
    new_leads = []

    print("🚀 RUN START")

    for q in queries:
        print("🔎", q)

        for start in range(0, 30, 10):
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

                if not profile or profile in existing:
                    continue

                s = score(snippet)

                if s < MIN_SCORE:
                    continue

                lead = {
                    "profile": profile,
                    "post": link,
                    "score": s,
                    "message": generate_msg(snippet),
                    "date": datetime.today().strftime('%Y-%m-%d')
                }

                new_leads.append(lead)
                existing.add(profile)

            time.sleep(1)

    save(new_leads)

    print(f"🔥 {len(new_leads)} nouveaux leads ajoutés")

if __name__ == "__main__":
    while True:
        run()
        print("⏸️ pause 3h...")
        time.sleep(10800)
