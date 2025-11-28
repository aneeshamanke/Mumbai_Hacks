import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../config/.env"))

from shared.tools import NewsTool

def test_news():
    print("Initializing NewsTool...")
    try:
        tool = NewsTool()
        query = "latest cricket news"
        print(f"Running news search for: '{query}'")
        result = tool.run({"query": query, "days": 3})
        print("\n--- Result ---")
        print(result)
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    test_news()
