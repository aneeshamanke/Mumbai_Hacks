"""Voting service skeleton that simulates reviewer votes."""

from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass
from typing import Dict, List

from shared.consensus import compute_confidence
from shared.storage import load_runs, update_run

@dataclass
class Vote:
    run_id: str
    user_id: str
    vote: int  # 1 = upvote, -1 = downvote
    weight: float
    rationale: str


class VotingService:
    def __init__(self) -> None:
        self.personas = self._load_personas()

    def _load_personas(self) -> List[Dict]:
        path = os.path.join(os.path.dirname(__file__), "..", "data", "mock_users.json")
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def fetch_relevant_reviewers(self, domain: str | None = None, location: str | None = None) -> List[Dict]:
        """Return top reviewers filtered by expertise/location."""
        candidates = []
        for persona in self.personas:
            score = persona["precision"]
            if domain in persona["expertise"]:
                score += 0.05
            if location and persona["location"].lower() == location.lower():
                score += 0.03
            candidates.append((score, persona))
        candidates.sort(key=lambda tup: tup[0], reverse=True)
        return [persona for _, persona in candidates[:5]]

    def simulate_vote(self, run_id: str, persona: Dict) -> Vote:
        weight = round(persona["precision"], 2)
        vote_value = 1 if random.random() < persona["precision"] else -1
        rationale = f"Auto-generated vote by {persona['name']} (precision={persona['precision']})"
        return Vote(run_id=run_id, user_id=persona["user_id"], vote=vote_value, weight=weight, rationale=rationale)


def process_runs(service: VotingService, required_votes: int = 3) -> None:
    runs = load_runs()
    for run_id, data in runs.items():
        if data.get("status") != "awaiting_votes":
            continue
        votes: List[Dict] = data.get("votes", [])
        if len(votes) >= required_votes:
            continue
        reviewers = service.fetch_relevant_reviewers(domain=data.get("domain") or "technology", location=None)
        for reviewer in reviewers[: required_votes - len(votes)]:
            vote = service.simulate_vote(run_id=run_id, persona=reviewer)
            votes.append(vote.__dict__)
        confidence = compute_confidence(votes)
        status = "completed" if len(votes) >= required_votes else "awaiting_votes"
        update_run(run_id, votes=votes, confidence=confidence, status=status)
        print(f"[voting] run_id={run_id} votes={len(votes)} confidence={confidence}")


def main() -> None:
    service = VotingService()
    while True:
        process_runs(service)
        time.sleep(2)


if __name__ == "__main__":
    main()
