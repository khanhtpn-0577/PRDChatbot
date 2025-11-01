from mcp.server.fastmcp import FastMCP
import requests
import os
from dotenv import load_dotenv
import uvicorn

# Load .env
load_dotenv()

mcp = FastMCP("Demo", stateless_http=True)

@mcp.tool()
def web_search(query: str, limit: int = 1) -> list: #limit: luong ket qua tra ve toi da
    """
    Search the web using Firecrawl.io and return summarized results.
    Args:
        query (str): The search query.
        limit (int): Number of results to return (should be 1).
    """
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError("Missing FIRECRAWL_API_KEY environment variable.")
    
    #search
    try:
        resp = requests.post(
            "https://api.firecrawl.dev/v1/search",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"query": query, "limit": limit},
            timeout=15 #timeout 15s
            )
        
        print("Firecrawl status:", resp.status_code)
        print("Firecrawl body:", resp.text[:500])
        resp.raise_for_status() #raise exception theo ma loi
        data = resp.json()
    except Exception as e:
        return [f"Error during web search: {str(e)}"]
    
    results = []
    for item in data.get("data", []):
        url = item.get("url")
        if not url:
            continue
        
        #scrape content from url
        try:
            scrape_resp = requests.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"url": url},
                timeout=30
            )
            print(f"Scrape {url[:50]}... status:", scrape_resp.status_code)
            scrape_resp.raise_for_status()
            scrape_data = scrape_resp.json()
            content = scrape_data.get("data", {}).get("markdown", "") or item.get("snippet")
        except Exception as e:
            content = f"Error scraping {url}: {str(e)}"
                
        results.append({
            "title": item.get("title"),
            "url": item.get("url"),
            "snippet": content[:1000]
        })
        
    return results or [{"message": "No results found."}]

if __name__ == "__main__":
    app = mcp.streamable_http_app()
    uvicorn.run(app, host="127.0.0.1", port=8081)