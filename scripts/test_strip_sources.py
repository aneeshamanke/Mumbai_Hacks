import re

def clean_answer(text):
    # Regex to remove "Sources:" or "References:" block at the end
    # Matches:
    # \n+          : One or more newlines
    # (\*\*|#+)?   : Optional bold or header marker
    # (Sources|References|Citations) : Keyword
    # .*           : Everything after (dotall)
    
    pattern = r"\n+(\*\*|#+\s)?(Sources|References|Citations).*?(\Z)"
    
    # We use re.DOTALL to match newlines in the "everything after" part
    cleaned = re.sub(pattern, "", text, flags=re.DOTALL | re.IGNORECASE)
    return cleaned.strip()

sample_text = """The CEO of Apple is Tim Cook.

**Sources:**
* [Link 1](http://example.com)
* [Link 2](http://example.org)"""

cleaned = clean_answer(sample_text)
print(f"Original length: {len(sample_text)}")
print(f"Cleaned length: {len(cleaned)}")
print("-" * 20)
print(cleaned)
print("-" * 20)
