import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../config/.env"))

from shared.tools import TavilySearchTool

def test_tavily():
    print("Initializing TavilySearchTool...")
    try:
        tool = TavilySearchTool()
        query = "What was Donald Trump's last foreign visit?"
        print(f"Running search for: '{query}'")
        result = tool.run({"query": query})
        print("\n--- Result ---")
        print(result)
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    test_tavily()
