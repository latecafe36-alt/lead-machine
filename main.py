import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

SENDERS = [
    "contact@stephanepatentes.com",
    "thomas@stephanepatentes.com",
    "vincent@stephanepatentes.com"
]

MAX_PER_ACCOUNT = 1
MAX_TOTAL = 3
MAX_THREADS = 5

CALENDLY_LINK = "https://calendly.com/stephane/30min"

queries = [
'site:linkedin.com/posts ("AI startup" OR "raising AI" OR "machine learning startup") ("Geneva" OR "Zurich" OR "Brussels" OR "Mons")',
'site:linkedin.com/in ("Founder" OR "CEO") "AI" ("raising" OR "funding") ("Geneva" OR "Zurich" OR "Brussels" OR "Mons")',
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

    for k in ["ai", "machine learning", "startup"]:
        if k in text:
            score += 2

    for k in ["raising", "funding", "seed"]:
        if k in text:
            score += 3

    if "ceo" in name.lower() or "founder" in name.lower():
        score += 2

    return score

# -------- DOMAIN --------
def find_domain(name):
    params = {"q": name + " startup", "api_key": SERPAPI_KEY}
    data = safe_request("https://serpapi.com/search", params)

    for r in data.get("organic_results", []):
        link = r.get("link", "")
        if ".com" in link:
            return link.split("/")[2]

    return ""

# -------- EMAIL --------
def find_email(name):
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

# -------- MESSAGE (IA simple) --------
def generate_message(name, snippet):
    first_name = name.split()[0] if name else "there"
    intro = snippet[:100] if snippet else "your recent AI work"

    return f"""Hey {first_name},

I saw this about you:
"{intro}"

Really interesting move in AI.

I’m currently working on SaaS & AI projects and exploring partnerships or funding opportunities.

Would you be open to a quick 10-min chat?

👉 {CALENDLY_LINK}

– Stephane
"""

# -------- FOLLOW-UP --------
def send_followup(email, name):
    first_name = name.split()[0] if name else "there"

    msg = f"""Hey {first_name},

Just following up in case you missed my previous message.

Let me know if it's relevant for you.

👉 {CALENDLY_LINK}

– Stephane
"""

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        message = Mail(
            from_email=SENDERS[0],
            to_emails=email,
            subject="Following up",
            html_content=msg.replace("\n", "<br>")
        )
        sg.send(message)
        print(f"🔁 Follow-up → {email}")
    except:
        pass

# -------- EMAIL SEND --------
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
    except:
        pass

# -------- PROCESS LEAD --------
def process_lead(r):
    link = r.get("link", "")
    name = r.get("title", "")
    snippet = r.get("snippet", "")

    score = score_lead(snippet, name)
    if score < 4:
        return None

    email, domain = find_email(name)

    return {
        "name": name,
        "link": link,
        "snippet": snippet,
        "email": email,
        "domain": domain,
        "score": score
    }

# -------- FOLLOW-UP CHECK --------
def process_followups():
    if not os.path.exists("leads.csv"):
        return

    df = pd.read_csv("leads.csv")
    today = datetime.today()

    for i, row in df.iterrows():
        if row["status"] == "sent":
            sent_date = datetime.strptime(row["date"], "%Y-%m-%d")

            if (today - sent_date).days >= 2:
                send_followup(row["email"], row["name"])
                df.at[i, "status"] = "followed"

    df.to_csv("leads.csv", index=False)

# -------- SCRAPE --------
def scrape():
    results = []
    sent_total = 0
    sent_per_account = {s: 0 for s in SENDERS}

    for query in queries:
        params = {"q": query, "num": 30, "api_key": SERPAPI_KEY}
        data = safe_request("https://serpapi.com/search", params)

        leads = data.get("organic_results", [])

        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(process_lead, r) for r in leads]

            for future in as_completed(futures):
                lead = future.result()
                if not lead:
                    continue

                email = lead["email"]
                name = lead["name"]
                snippet = lead["snippet"]

                if email and sent_total < MAX_TOTAL:
                    available = [s for s in SENDERS if sent_per_account[s] < MAX_PER_ACCOUNT]
                    if not available:
                        break

                    sender = random.choice(available)
                    msg = generate_message(name, snippet)

                    send_email(email, msg, sender)

                    sent_per_account[sender] += 1
                    sent_total += 1

                    time.sleep(random.randint(5, 15))

                results.append({
                    "name": name,
                    "linkedin": lead["link"],
                    "email": email,
                    "domain": lead["domain"],
                    "score": lead["score"],
                    "status": "sent" if email else "no_email",
                    "date": datetime.today().strftime('%Y-%m-%d')
                })

    return pd.DataFrame(results)

# -------- SAVE --------
def save(df):
    if os.path.exists("leads.csv"):
        df.to_csv("leads.csv", mode="a", header=False, index=False)
    else:
        df.to_csv("leads.csv", index=False)

# -------- RUN --------
if __name__ == "__main__":
    print("🚀 Machine lancée...")

    while True:
        process_followups()
        df = scrape()
        save(df)
        print("✅ Batch terminé")
        time.sleep(21600)
