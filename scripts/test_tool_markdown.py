import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.tools import TavilySearchTool
import re
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../config/.env"))

def has_markdown(text):
    # Check for common Markdown indicators
    indicators = [
        r"\*\*", # Bold
        r"__",   # Bold
        r"\[.*?\]\(.*?\)", # Link
        r"^#+\s", # Header (start of line)
        r"`",    # Code
    ]
    for pattern in indicators:
        if re.search(pattern, text, re.MULTILINE):
            return True, pattern
    return False, None

def test_tavily():
    tool = TavilySearchTool()
    print("Running Web Search for 'CEO of Apple'...")
    result = tool.run("CEO of Apple")
    print("-" * 20)
    print(result)
    print("-" * 20)
    
    is_markdown, pattern = has_markdown(result)
    if is_markdown:
        print(f"FAILED: Markdown detected! Pattern: {pattern}")
    else:
        print("PASSED: No Markdown detected.")

if __name__ == "__main__":
    test_tavily()
