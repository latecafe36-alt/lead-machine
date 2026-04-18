import requests
import csv
import time
import os

# 🔐 API KEY depuis Railway (OBLIGATOIRE)
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    print("❌ ERREUR: API_KEY manquante !")
    exit()

print("✅ API KEY détectée")

# 🌍 VILLES
cities = [
    "Paris", "London", "Berlin", "Geneva", "Brussels"
]

# 🔎 QUERIES (moins strictes pour tester)
base_queries = [
    '"raising funds"',
    '"looking for investors"',
    '"startup fundraising"',
    '"seed round"',
    '"series A"'
]

# 🧠 SCORE
def score(text):
    t = text.lower()
    s = 0

    keywords = {
        "raising": 3,
        "funding": 3,
        "investors": 4,
        "seed": 3,
        "series a": 4,
        "pre-seed": 3,
        "capital": 2,
        "vc": 3,
        "angel": 3
    }

    for k, v in keywords.items():
        if k in t:
            s += v

    return s


# 📊 STOCKAGE
leads = []
seen_links = set()

print("🚀 START SCRAPING...\n")

# 🔁 LOOP
for city in cities:
    for base in base_queries:

        query = f'site:linkedin.com/posts {base} "{city}"'
        print(f"\n🔎 QUERY: {query}")

        # ⚠️ TEST: seulement 2 pages (plus rapide)
        for start in range(0, 20, 10):

            params = {
                "engine": "google",
                "q": query,
                "api_key": API_KEY,
                "start": start,
                "num": 10
                # ❌ on enlève tbs au début
            }

            try:
                response = requests.get("https://serpapi.com/search", params=params)
                data = response.json()

                # 🔥 DEBUG
                if "error" in data:
                    print("❌ SERPAPI ERROR:", data["error"])
                    continue

                results = data.get("organic_results", [])

                print(f"👉 {len(results)} résultats")

                for r in results:
                    link = r.get("link", "")
                    title = r.get("title", "")
                    snippet = r.get("snippet", "")

                    text = title + " " + snippet
                    s = score(text)

                    # 🎯 filtre
                    if link not in seen_links and s >= 3:
                        seen_links.add(link)

                        leads.append({
                            "title": title,
                            "link": link,
                            "snippet": snippet,
                            "score": s,
                            "city": city
                        })

            except Exception as e:
                print("❌ ERREUR:", e)

            time.sleep(1)

# 💾 SAVE
with open("leads.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["title", "link", "snippet", "score", "city"])
    writer.writeheader()
    writer.writerows(leads)

print(f"\n🔥 {len(leads)} LEADS TROUVÉS")
print("✅ Sauvegardé dans leads.csv")
