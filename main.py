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

# -------- MESSAGE --------
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
