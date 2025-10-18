from mcp.server.fastmcp import FastMCP
import requests
import os
from dotenv import load_dotenv
import uvicorn

# Load .env
load_dotenv()

mcp = FastMCP("Demo", stateless_http=True)

@mcp.tool()
def web_search(query: str, limit: int = 3) -> list: #limit: luong ket qua tra ve toi da
    """
    Search the web using Firecrawl.io and return summarized results.
    Args:
        query (str): The search query.
        limit (int): Number of results to return (default=3).
    """
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError("Missing FIRECRAWL_API_KEY environment variable.")
    
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
        results.append({
            "title": item.get("title"),
            "url": item.get("url"),
            "snippet": item.get("snippet") or item.get("description")
        })
        
    return results or [{"message": "No results found."}]

if __name__ == "__main__":
    app = mcp.streamable_http_app()
    uvicorn.run(app, host="127.0.0.1", port=8081)