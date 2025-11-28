"""Computes leaderboard + rewards from vote history (skeleton)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import List


@dataclass
class UserStat:
    user_id: str
    name: str
    precision: float
    attempts: int

    @property
    def points(self) -> int:
        return int(self.precision * 100 * min(self.attempts, 5))

    @property
    def tier(self) -> str:
        if self.points >= 400:
            return "Platinum"
        if self.points >= 250:
            return "Gold"
        if self.points >= 150:
            return "Silver"
        return "Bronze"


def load_user_stats() -> List[UserStat]:
    path = os.path.join(os.path.dirname(__file__), "..", "data", "mock_users.json")
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return [UserStat(user_id=item["user_id"], name=item["name"], precision=item["precision"], attempts=item["attempts"]) for item in raw]


def main() -> None:
    stats = sorted(load_user_stats(), key=lambda user: user.points, reverse=True)
    print("Leaderboard snapshot:")
    for idx, stat in enumerate(stats, start=1):
        print(f"{idx}. {stat.name} ({stat.user_id}) → precision={stat.precision:.2f} attempts={stat.attempts} points={stat.points} tier={stat.tier}")


if __name__ == "__main__":
    main()
