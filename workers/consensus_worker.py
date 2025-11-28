"""Consensus worker recomputes weighted verdicts from votes (skeleton)."""

from __future__ import annotations

from shared.consensus import compute_confidence


def main() -> None:
    demo_votes = [
        {"run_id": "demo-run", "vote": 1, "weight": 0.9},
        {"run_id": "demo-run", "vote": 1, "weight": 0.8},
        {"run_id": "demo-run", "vote": -1, "weight": 0.4},
    ]
    confidence = compute_confidence(demo_votes)
    verdict = "supported" if confidence >= 0.6 else "contested"
    print(f"[consensus] run_id=demo-run confidence={confidence} verdict={verdict}")


if __name__ == "__main__":
    main()
