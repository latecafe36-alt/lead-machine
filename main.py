import requests
import pandas as pd
from datetime import datetime
import os
import time
import random

SERP_API_KEY = os.getenv("SERP_API_KEY")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")

queries = [
    'site:linkedin.com/in ("CEO" OR "Founder") "SaaS" "Paris" funding',
    'site:linkedin.com/in ("CEO" OR "Founder") "AI" "Europe" seed',
    'site:linkedin.com/in ("co-founder") startup "Geneva" raised'
]

# -------- SCORE --------
def score_lead(snippet, name):
    text = (snippet or "").lower()
    score = 0

    for k in ["funding", "raised", "seed", "series a"]:
        if k in text:
            score += 3

    for k in ["startup", "saas", "ai"]:
        if k in text:
            score += 1

    if "ceo" in name.lower() or "founder" in name.lower():
        score += 2

    if score >= 5:
        return "HOT"
    elif score >= 3:
        return "WARM"
    return "COLD"

# -------- DOMAIN --------
def find_domain(name):
    params = {
        "q": name + " company",
        "api_key": SERP_API_KEY
    }

    try:
        res = requests.get("https://serpapi.com/search", params=params).json()
        for r in res.get("organic_results", []):
            link = r.get("link", "")
            if ".com" in link:
                return link.split("/")[2]
    except:
        pass

    return ""

# -------- EMAIL --------
def find_email(name):
    domain = find_domain(name)
    if not domain:
        return ""

    params = {
        "domain": domain,
        "full_name": name,
        "api_key": HUNTER_API_KEY
    }

    try:
        r = requests.get("https://api.hunter.io/v2/email-finder", params=params).json()
        if r.get("data") and r["data"].get("email"):
            return r["data"]["email"]
    except:
        pass

    return ""

# -------- MESSAGE --------
def generate_message(name, snippet):
    first_name = name.split()[0] if name else "there"
    company = "your company"

    return f"""Hey {first_name},

I came across {company} and thought there might be a fit.

I'm currently working on SaaS projects and looking for potential partners or people interested in funding opportunities.

Would you be open to a quick exchange?

– Thomas"""

# -------- SCRAPE --------
def scrape():
    results = []

    for query in queries:
        params = {
            "q": query,
            "num": 100,
            "api_key": SERP_API_KEY
        }

        data = requests.get("https://serpapi.com/search", params=params).json()

        for r in data.get("organic_results", []):
            link = r.get("link", "")
            name = r.get("title", "")
            snippet = r.get("snippet", "")

            if "linkedin.com/in" in link:
                score = score_lead(snippet, name)

                if score == "COLD":
                    continue

                email = find_email(name)
                message = generate_message(name, snippet)

                results.append({
                    "name": name,
                    "linkedin": link,
                    "email": email,
                    "score": score,
                    "message": message,
                    "date": datetime.today().strftime('%Y-%m-%d')
                })

                time.sleep(random.randint(10, 30))

    return pd.DataFrame(results)

# -------- SAVE --------
def save(df):
    if os.path.exists("leads.csv"):
        df.to_csv("leads.csv", mode='a', header=False, index=False)
    else:
        df.to_csv("leads.csv", index=False)

# -------- RUN LOOP --------
if _name_ == "_main_":
    print("Machine lancée 🚀")

    while True:
        df = scrape()
        save(df)
        print("Batch terminé, pause...")
        time.sleep(21600)  # 6 heures
