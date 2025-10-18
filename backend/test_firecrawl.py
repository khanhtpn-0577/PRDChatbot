import requests, os
from dotenv import load_dotenv

# Load .env file
load_dotenv()
api_key = os.getenv("FIRECRAWL_API_KEY")

if not api_key:
    raise ValueError("Missing FIRECRAWL_API_KEY in .env")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# --- STEP 1: SEARCH ---
search_resp = requests.post(
    "https://api.firecrawl.dev/v1/search",
    headers=headers,
    json={"query": "what is artificial intelligent", "limit": 2},
    timeout=20
)

print("Search status:", search_resp.status_code)
print("Search response text:", search_resp.text[:400], "\n")

if search_resp.status_code != 200:
    raise SystemExit("Search request failed.")

search_data = search_resp.json()
results = search_data.get("data", [])

if not results:
    raise SystemExit("No search results found.")

# --- STEP 2: SCRAPE ---
first_url = results[0].get("url")
print("Scraping URL:", first_url)

scrape_resp = requests.post(
    "https://api.firecrawl.dev/v1/scrape",
    headers=headers,
    json={"url": first_url},
    timeout=30
)

print("Scrape status:", scrape_resp.status_code)
scrape_data = scrape_resp.json()
markdown_text = scrape_data.get("data", {}).get("markdown", "")
title = scrape_data.get("data", {}).get("metadata", {}).get("title", "")
url = scrape_data.get("data", {}).get("metadata", {}).get("url", "")

print("Title:", title)
print("URL:", url)
print("Markdown preview:", markdown_text[:500])
