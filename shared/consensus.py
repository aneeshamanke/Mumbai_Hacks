"""Utilities for vote weighting and confidence scoring."""

from __future__ import annotations

from typing import Iterable, Mapping


def compute_confidence(votes: Iterable[Mapping[str, float]]) -> float:
    """Return weighted confidence score between 0 and 1."""
    weighted = sum(v["vote"] * v["weight"] for v in votes)
    max_weight = sum(abs(v["weight"]) for v in votes) or 1
    normalized = (weighted / max_weight + 1) / 2  # map [-1,1] -> [0,1]
    return round(normalized, 3)
