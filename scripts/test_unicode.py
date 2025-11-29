import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.tools import TavilySearchTool
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../config/.env"))

def test_unicode_normalization():
    tool = TavilySearchTool()
    
    # Text with non-breaking space (\u00a0) and curly quote (\u2019)
    raw_text = "Apple\u00a0Inc. is the world\u2019s most valuable company."
    expected_text = "Apple Inc. is the world's most valuable company."
    
    normalized = tool.strip_markdown(raw_text)
    
    print(f"Raw:      '{raw_text}'")
    print(f"Normalized: '{normalized}'")
    print(f"Expected:   '{expected_text}'")
    
    if normalized == expected_text:
        print("PASSED: Unicode normalized correctly.")
    else:
        print("FAILED: Unicode normalization failed.")

if __name__ == "__main__":
    test_unicode_normalization()
