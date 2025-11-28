from duckduckgo_search import DDGS
import json

def test_search(query, region='in-en'):
    print(f"--- Testing '{query}' with region='{region}' ---")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, region=region, max_results=3))
            if results:
                for r in results:
                    print(f"- {r['title']}: {r['href']}")
            else:
                print("No results found.")
    except Exception as e:
        print(f"Error: {e}")

print("Testing DuckDuckGo Search...")
test_search("Donald Trump last foreign visit", region="in-en")
test_search("Donald Trump last foreign visit", region="us-en")
test_search("Donald Trump last foreign visit", region="wt-wt")
