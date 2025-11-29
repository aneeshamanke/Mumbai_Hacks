import re

def extract_citations(text):
    citations = []
    # Regex to match: - **Title**\n  Content\n  Source: URL
    # It needs to handle the content being multi-line or containing newlines.
    # The pattern repeats.
    
    # Pattern breakdown:
    # - \*\*  : Match "- **" literal
    # (.*?)   : Capture Title (non-greedy)
    # \*\*    : Match "**" literal
    # \s+     : Match whitespace/newlines
    # .*?     : Match content (non-greedy)
    # Source: : Match "Source: " literal
    # (.*?)   : Capture URL (non-greedy)
    # (?=\n\n|\Z) : Lookahead for double newline or end of string
    
    pattern = r"- \*\*(.*?)\*\*\s+.*?\s+Source: (.*?)(?=\n\n|\Z)"
    
    matches = re.finditer(pattern, text, re.DOTALL)
    for match in matches:
        citations.append({
            "title": match.group(1).strip(),
            "url": match.group(2).strip()
        })
    return citations

sample_text = """- **Title One**
  Some content here.
  Source: https://example.com/1

- **Title Two**
  Multi-line
  content here.
  Source: https://example.com/2"""

print(extract_citations(sample_text))
