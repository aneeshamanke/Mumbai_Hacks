"""Automated moderator resolution worker for claim verification."""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from shared.storage import load_runs, update_run, get_run

SOURCES_PATH = os.path.join(os.path.dirname(__file__), "data", "credible_sources.json")

def load_credible_sources() -> Dict[str, List[str]]:
    """Load the credible sources registry."""
    try:
        with open(SOURCES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[resolution] Warning: {SOURCES_PATH} not found")
        return {}


SOURCES = load_credible_sources()


def get_sources_for_topics(topics: List[str]) -> List[str]:
    """Map claim topics to credible domains."""
    domains = []
    for topic in topics:
        topic_lower = topic.lower()
        for key in SOURCES:
            if topic_lower in key.lower():
                domains.extend(SOURCES[key])
    return list(set(domains))


def search_credible_sources(claim_text: str, domains: List[str]) -> Optional[int]:
    """Search credible sources for claim verification.
    
    Uses Tavily API for web search with domain filtering.
    Tavily is installed via requirements.txt (tavily-python).
    
    Returns:
        1 for TRUE (confirmed)
        -1 for FALSE (denied)
        None for UNVERIFIABLE
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("[resolution] TAVILY_API_KEY not set, cannot verify claims")
        return None
    
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        
        site_filter = " OR ".join([f"site:{d}" for d in domains[:5]])
        query = f"{claim_text} ({site_filter})"
        
        response = client.search(query, search_depth="advanced", max_results=5)
        results = response.get("results", [])
        
        if not results:
            return None
        
        combined_content = " ".join([r.get("content", "") for r in results]).lower()
        
        confirmation_patterns = [
            r"\b(confirmed|verified|true|accurate|correct|factual)\b",
            r"\b(according to|sources confirm|officials say)\b",
            r"\b(is true|has been confirmed)\b"
        ]
        
        denial_patterns = [
            r"\b(false|fake|hoax|misleading|debunked|incorrect)\b",
            r"\b(misinformation|disinformation|not true)\b",
            r"\b(claim is false|has been debunked)\b"
        ]
        
        confirmation_score = sum(
            len(re.findall(pattern, combined_content))
            for pattern in confirmation_patterns
        )
        denial_score = sum(
            len(re.findall(pattern, combined_content))
            for pattern in denial_patterns
        )
        
        if denial_score > confirmation_score and denial_score >= 2:
            return -1
        elif confirmation_score > denial_score and confirmation_score >= 2:
            return 1
        
        return None
        
    except Exception as e:
        print(f"[resolution] Search error: {e}")
        return None


def resolve_pending_claims() -> None:
    """Check and resolve pending claims older than 1 hour."""
    runs = load_runs()
    resolved_count = 0
    
    for run_id, run in runs.items():
        if run.get("ground_truth") is not None:
            continue
        
        created_str = run.get("created_at")
        if created_str:
            try:
                created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            except ValueError:
                created = datetime.now()
        else:
            continue
        
        age = datetime.now() - created.replace(tzinfo=None)
        if age < timedelta(hours=1):
            continue
        
        topics = run.get("topics", ["General"])
        sources = get_sources_for_topics(topics)
        
        if not sources:
            sources = SOURCES.get("General", [])
        
        if not sources:
            continue
        
        print(f"[resolution] Checking claim {run_id}: {run.get('prompt', '')[:50]}...")
        verdict = search_credible_sources(run["prompt"], sources)
        
        if verdict is not None:
            update_run(
                run_id,
                ground_truth=verdict,
                status="verified",
                resolved_at=datetime.now().isoformat(),
                resolved_by="moderator_agent"
            )
            resolved_count += 1
            print(f"[resolution] Resolved {run_id}: {'TRUE' if verdict == 1 else 'FALSE'}")
        else:
            update_run(
                run_id,
                ground_truth=None,
                status="unverifiable",
                resolved_at=datetime.now().isoformat(),
                resolved_by="moderator_agent"
            )
            print(f"[resolution] Marked {run_id} as unverifiable")
    
    if resolved_count > 0:
        print(f"[resolution] Resolved {resolved_count} claims this cycle")


def main() -> None:
    """Main loop - runs hourly."""
    print("[resolution] Starting moderator resolution worker...")
    print(f"[resolution] Loaded {len(SOURCES)} source categories")
    
    while True:
        try:
            resolve_pending_claims()
        except Exception as e:
            print(f"[resolution] Error in resolution cycle: {e}")
        
        print("[resolution] Sleeping for 1 hour...")
        time.sleep(3600)


if __name__ == "__main__":
    main()
