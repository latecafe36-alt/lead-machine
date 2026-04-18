import requests
import time
import csv

API_KEY = "TA_CLE_SERPAPI_ICI"

QUERIES = [
    'site:linkedin.com/in "founder startup"',
    'site:linkedin.com/in "CEO startup"',
    'site:linkedin.com/in "co-founder startup"',
    'site:linkedin.com/in "entrepreneur startup"',
    'site:linkedin.com/in "startup CEO"',
]

def search_google(query):
    url = "https://serpapi.com/search"
    
    params = {
        "q": query,
        "api_key": API_KEY,
        "engine": "google",
        "num": 20
    }

    response = requests.get(url, params=params)
    data = response.json()

    results = []

    if "organic_results" in data:
        for result in data["organic_results"]:
            link = result.get("link", "")
            title = result.get("title", "")
            snippet = result.get("snippet", "")

            if "linkedin.com/in/" in link:
                results.append({
                    "name": title,
                    "link": link,
                    "bio": snippet
                })

    return results


def main():
    all_leads = []

    print("🚀 Scraping lancé...\n")

    for query in QUERIES:
        print(f"🔎 Query: {query}")
        leads = search_google(query)

        print(f"👉 {len(leads)} résultats trouvés\n")

        all_leads.extend(leads)
        time.sleep(2)

    # SUPPRIMER DOUBLONS
    unique = {lead["link"]: lead for lead in all_leads}
    leads = list(unique.values())

    print(f"\n🔥 {len(leads)} leads uniques trouvés\n")

    # AFFICHAGE
    for lead in leads:
        print(f"👤 {lead['name']}")
        print(f"🔗 {lead['link']}")
        print(f"📝 {lead['bio']}")
        print("-" * 50)

    # SAVE CSV
    with open("leads.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "link", "bio"])
        writer.writeheader()
        writer.writerows(leads)

    print("\n✅ Leads sauvegardés dans leads.csv")


if __name__ == "__main__":
    main()
