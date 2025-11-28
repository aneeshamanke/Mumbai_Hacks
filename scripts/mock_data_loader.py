"""Seeds MongoDB with dummy reviewer personas for the MVP."""

from __future__ import annotations

import json
import os
from typing import List

try:
    from pymongo import MongoClient
except ImportError:  # pragma: no cover - optional dependency for skeleton
    MongoClient = None  # type: ignore


def load_personas() -> List[dict]:
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "mock_users.json")
    with open(data_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def seed_mongo(uri: str, personas: List[dict]) -> None:
    if MongoClient is None:
        print("pymongo not installed; skipping DB seed.")
        return

    client = MongoClient(uri)
    db = client.get_default_database()
    collection = db["users"]
    for persona in personas:
        collection.update_one({"user_id": persona["user_id"]}, {"$set": persona}, upsert=True)
    print(f"Seeded {len(personas)} personas into MongoDB ({db.name}.users).")


def main() -> None:
    personas = load_personas()
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/misinformation")
    seed_mongo(mongo_uri, personas)


if __name__ == "__main__":
    main()
