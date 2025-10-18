import requests, os
from dotenv import load_dotenv

# Load .env
load_dotenv()
api_key = os.getenv("FIRECRAWL_API_KEY")

resp = requests.post(
    "https://api.firecrawl.dev/v1/search",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json={"query": "n8n facebook graph api upload post", "limit": 2}
)
print(resp.status_code, resp.text)
