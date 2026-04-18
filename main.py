import requests
import pandas as pd
from datetime import datetime
import os
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# -------- CONFIG --------
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

SENDERS = [
    "contact@stephanepatentes.com",
    "thomas@stephanepatentes.com",
    "vincent@stephanepatentes.com"
]

MAX_PER_ACCOUNT = 1
MAX_TOTAL = 5
MAX_THREADS = 5

CALENDLY_LINK = "https://calendly.com/stephane/30min"

queries = [
    'site:linkedin.com/in ("Founder" OR "CEO") "AI" ("raising" OR "funding") ("Geneva" OR "Zurich" OR "Brussels")',
]

# -------- SAFE REQUEST --------
def safe_request(url, params, retries=3):
    for _ in range(retries):
        try:
            res = requests.get(url, params=params, timeout=10)
            return res.json()
        except Exception as e:
            print("⚠️ Request error:", e)
            time.sleep(random.randint(1, 3))
    return {}

# -------- SCORE --------
def score_lead(snippet, name):
    text = (snippet or "").lower()
    score = 0

    if "ai" in text:
        score += 2
    if "funding" in text or "raising" in text:
        score += 3
    if "ceo" in name.lower() or "founder" in name.lower():
        score += 2

    return score

# -------- FIND DOMAIN --------
def find_domain(name):
    try:
        params = {"q": name + " startup", "api_key": SERPAPI_KEY}
        data = safe_request("https://serpapi.com/search", params)

        for r in data.get("organic_results", []):
            link = r.get("link", "")
            if ".com" in link:
                return link.split("/")[2]
    except Exception as e:
        print("⚠️ Domain error:", e)

    return ""

# -------- FIND EMAIL --------
def find_email(name):
    try:
        domain = find_domain(name)
        if not domain:
            return "", ""

        params = {
            "domain": domain,
            "full_name": name,
            "api_key": HUNTER_API_KEY
        }

        data = safe_request("https://api.hunter.io/v2/email-finder", params)

        if data.get("data") and data["data"].get("email"):
            return data["data"]["email"], domain

        return "", domain

    except Exception as e:
        print("⚠️ Email lookup error:", e)
        return "", ""

# -------- GENERATE MESSAGE --------
def generate_message(name, snippet):
    first_name = name.split()[0] if name else "there"
    intro = snippet[:100] if snippet else "your AI project"

    return f"""Hey {first_name},

I saw this about you:
"{intro}"

Really interesting.

I'm working on AI & SaaS projects and exploring partnerships.

Quick 10min chat?

👉 {CALENDLY_LINK}

– Stephane
"""

# -------- SEND EMAIL --------
def send_email(to_email, content, sender):
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        message = Mail(
            from_email=sender,
            to_emails=to_email,
            subject="Quick question",
            html_content=content.replace("\n", "<br>")
        )
        sg.send(message)
        print(f"📨 {sender} → {to_email}")

    except Exception as e:
        print("❌ Email error:", e)

# -------- PROCESS LEAD --------
def process_lead(r):
    try:
        name = r.get("title", "")
        snippet = r.get("snippet", "")

        score = score_lead(snippet, name)
        if score < 4:
            return None

        email, domain = find_email(name)

        return {
            "name": name,
            "linkedin": r.get("link", ""),
            "email": email,
            "domain": domain,
            "score": score,
            "snippet": snippet
        }

    except Exception as e:
        print("⚠️ Lead error:", e)
        return None

# -------- SCRAPE --------
def scrape():
    results = []
    sent_total = 0
    sent_per_account = {s: 0 for s in SENDERS}

    for query in queries:
        print("🔎 Query:", query)

        params = {"q": query, "num": 20, "api_key": SERPAPI_KEY}
        data = safe_request("https://serpapi.com/search", params)

        leads = data.get("organic_results", [])

        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(process_lead, r) for r in leads]

            for future in as_completed(futures):
                lead = future.result()
                if not lead:
                    continue

                email = lead["email"]

                # Envoi limité
                if email and sent_total < MAX_TOTAL:
                    available = [s for s in SENDERS if sent_per_account[s] < MAX_PER_ACCOUNT]

                    if available:
                        sender = random.choice(available)
                        msg = generate_message(lead["name"], lead["snippet"])

                        send_email(email, msg, sender)

                        sent_per_account[sender] += 1
                        sent_total += 1

                        time.sleep(random.randint(5, 10))

                results.append({
                    "name": lead["name"],
                    "linkedin": lead["linkedin"],
                    "email": email,
                    "domain": lead["domain"],
                    "score": lead["score"],
                    "status": "sent" if email else "no_email",
                    "date": datetime.today().strftime('%Y-%m-%d')
                })

    return pd.DataFrame(results)

# -------- SAVE --------
def save(df):
    try:
        if df.empty:
            return

        if os.path.exists("leads.csv"):
            df.to_csv("leads.csv", mode="a", header=False, index=False)
        else:
            df.to_csv("leads.csv", index=False)

        print("💾 Leads sauvegardés")

    except Exception as e:
        print("❌ Save error:", e)

# -------- MAIN LOOP --------
if __name__ == "__main__":
    print("🚀 Machine lancée en continu")

    while True:
        try:
            print("🔄 Nouveau batch")

            df = scrape()
            save(df)

            print("✅ Batch terminé")
            print("⏳ Pause 1h")

            time.sleep(3600)

        except Exception as e:
            print("💥 Crash global:", e)
            time.sleep(60)
