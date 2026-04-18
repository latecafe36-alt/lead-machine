import requests
import csv
import time

API_KEY = ""  # ← mets ta clé ici

# 🌍 VILLES CIBLÉES
cities = [
    # 🇨🇭 Suisse
    "Zurich", "Geneva", "Lausanne", "Basel", "Bern", "Zug",
    "Lucerne", "St Gallen", "Winterthur",

    # 🇧🇪 Belgique
    "Brussels", "Antwerp", "Ghent", "Liege",
    "Charleroi", "Namur", "Leuven"
]

# 🔎 QUERIES ULTRA CIBLÉES (levée de fonds)
base_queries = [
    '"raising funds" startup',
    '"looking for investors" startup',
    '"seed round" startup',
    '"pre-seed startup"',
    '"series A startup"',
    '"raising capital startup"',
    '"we are raising startup"',
    '"startup fundraising"',
    '"looking for VC startup"',
    '"angel investors startup"'
]

# 🧠 SCORING LEAD
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

# 🔁 LOOP QUERIES + VILLES
for city in cities:
    for base in base_queries:

        query = f'site:linkedin.com/posts {base} "{city}"'
        print(f"🔎 {query}")

        # 🔁 MULTI-PAGES (100 résultats)
        for start in range(0, 100, 10):

            params = {
                "engine": "google",
                "q": query,
                "api_key": API_KEY,
                "start": start,
                "num": 10,
                "tbs": "qdr:d"  # 🔥 derniers 24h
            }

            try:
                response = requests.get("https://serpapi.com/search", params=params)
                data = response.json()

                results = data.get("organic_results", [])

                print(f"👉 {len(results)} résultats (page {start//10 + 1})")

                for r in results:
                    link = r.get("link", "")
                    title = r.get("title", "")
                    snippet = r.get("snippet", "")

                    text = title + " " + snippet
                    s = score(text)

                    # 🎯 filtre qualité
                    if link not in seen_links and s >= 5:
                        seen_links.add(link)

                        leads.append({
                            "title": title,
                            "link": link,
                            "snippet": snippet,
                            "score": s,
                            "city": city
                        })

            except Exception as e:
                print("❌ erreur :", e)

            time.sleep(1)  # anti-ban

# 💾 SAVE CSV
with open("leads.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["title", "link", "snippet", "score", "city"])
    writer.writeheader()
    writer.writerows(leads)

print(f"\n🔥 {len(leads)} LEADS TROUVÉS")
print("✅ Sauvegardé dans leads.csv")
