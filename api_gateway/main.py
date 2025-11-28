"""FastAPI entrypoint for the misinformation MVP."""

from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from shared.storage import create_run, enqueue_job, get_run, update_run

app = FastAPI(title="Misinformation Agentic Workflow")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PromptRequest(BaseModel):
    prompt: str = Field(..., min_length=4, max_length=2000)
    user_id: str | None = None


class Evidence(BaseModel):
    tool_name: str
    content: str
    metadata: Dict[str, Any]


class VotePayload(BaseModel):
    user_id: str
    vote: int
    weight: float
    rationale: str


class PromptResponse(BaseModel):
    run_id: str
    status: str
    provisional_answer: str | None = None
    confidence: Optional[float] = None
    votes: List[VotePayload] | None = None
    evidence: List[Evidence] | None = None


class LeaderboardEntry(BaseModel):
    user_id: str
    name: str
    precision: float
    attempts: int
    points: int
    tier: str


class LeaderboardResponse(BaseModel):
    entries: List[LeaderboardEntry]


def enqueue_prompt(run_id: str, payload: Dict[str, Any]) -> None:
    """Push job into JSON-backed queue for orchestrator."""
    enqueue_job(payload)


def fetch_leaderboard() -> List[Dict[str, Any]]:
    """Loads leaderboard data from Mongo or mock JSON."""
    # In MVP we just mirror mock data; cron should write a cached snapshot later.
    import json

    mock_path = os.path.join(os.path.dirname(__file__), "..", "data", "mock_users.json")
    with open(mock_path, "r", encoding="utf-8") as fh:
        users = json.load(fh)

    leaderboard = []
    for user in users:
        rewards = user.get("rewards", {})
        leaderboard.append(
            {
                "user_id": user["user_id"],
                "name": user["name"],
                "precision": user["precision"],
                "attempts": user["attempts"],
                "points": rewards.get("points", 0),
                "tier": rewards.get("tier", "Bronze"),
            }
        )
    return leaderboard


@app.post("/prompts", response_model=PromptResponse)
async def create_prompt(request: PromptRequest) -> PromptResponse:
    if not request.prompt.strip():
        raise HTTPException(status_code=422, detail="Prompt cannot be empty.")

    run_id = str(uuid.uuid4())
    run_payload = {
        "run_id": run_id,
        "prompt": request.prompt,
        "requester": request.user_id or "anon",
        "status": "queued",
        "provisional_answer": None,
        "votes": [],
        "confidence": None,
        "evidence": [],
    }
    create_run(run_id, run_payload)
    enqueue_prompt(run_id, payload=run_payload)
    return PromptResponse(run_id=run_id, status="queued", provisional_answer=None, votes=[], confidence=None, evidence=[])


@app.get("/runs/{run_id}", response_model=PromptResponse)
async def get_run_status(run_id: str) -> PromptResponse:
    """Expose run status for the frontend demo."""
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")
    if not run.get("provisional_answer"):
        # fallback text so frontend always renders content during demo
        run["provisional_answer"] = "[Demo answer] Gemini + search summary will appear here."
        update_run(run_id, **run)
    return PromptResponse(
        run_id=run["run_id"],
        status=run["status"],
        provisional_answer=run.get("provisional_answer"),
        confidence=run.get("confidence"),
        votes=run.get("votes"),
        evidence=run.get("evidence"),
    )


@app.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard() -> LeaderboardResponse:
    entries = [LeaderboardEntry(**entry) for entry in fetch_leaderboard()]
    return LeaderboardResponse(entries=entries)
