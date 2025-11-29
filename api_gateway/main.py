"""FastAPI entrypoint for VeriVerse misinformation detection."""

from __future__ import annotations
import os
import uuid
import random
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from shared.storage import create_run, enqueue_job, get_run, update_run

app = FastAPI(title="VeriVerse Misinformation API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo user data with enriched profiles
DEMO_VOTERS = [
    {
        "user_id": "aakash",
        "name": "Aakash Kumar",
        "location": "Mumbai",
        "expertise": ["Technology", "Sports"],
        "precision": 0.88,
    },
    {
        "user_id": "aneesha",
        "name": "Aneesha Manke",
        "location": "Nagpur",
        "expertise": ["Business", "Product", "AI", "Finance"],
        "precision": 0.92,
    },
    {
        "user_id": "shaurya",
        "name": "Shaurya Negi",
        "location": "Dehradun",
        "expertise": ["Finance", "Geography", "Tech"],
        "precision": 0.88,
    },
    {
        "user_id": "parth",
        "name": "Parth Joshi",
        "location": "Gujarat",
        "expertise": ["Technology", "Food", "India"],
        "precision": 0.82,
    },
]


class PromptRequest(BaseModel):
    prompt: str = Field(..., min_length=4, max_length=2000)
    user_id: str | None = None


class Evidence(BaseModel):
    tool_name: str
    content: str


class VotePayload(BaseModel):
    user_id: str
    name: str          
    location: str       
    expertise: List[str]  
    vote: int
    weight: float
    rationale: str
    precision: float   


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


def generate_demo_votes(prompt: str, author_user_id: str | None = None) -> List[Dict[str, Any]]:
    """Generate realistic demo votes based on prompt content.
    
    Args:
        prompt: The claim text to analyze for topic matching
        author_user_id: The user_id of the claim author (excluded from voters)
    """
    
    # Determine topic from prompt
    prompt_lower = prompt.lower()

    if any(word in prompt_lower for word in ["tech", "ai", "software", "app"]):
        topic = "Technology"
    elif any(word in prompt_lower for word in ["market", "stock", "finance", "economy", "rbi"]):
        topic = "Finance"
    elif any(word in prompt_lower for word in ["cricket", "sports", "ipl"]):
        topic = "Sports"
    elif any(word in prompt_lower for word in ["mumbai", "india", "delhi", "bangalore"]):
        topic = "India"
    else:
        topic = "General"
    
    # Filter out the claim author from eligible voters
    eligible_voters = [v for v in DEMO_VOTERS if v["user_id"] != author_user_id]
    
    if not eligible_voters:
        return []
    
    # Select 2-4 voters (or fewer if not enough eligible)
    num_voters = min(random.randint(2, 4), len(eligible_voters))
    selected_voters = random.sample(eligible_voters, num_voters)
    
    votes = []
    for voter in selected_voters:
        # Higher weight if expertise matches
        matches = topic in voter["expertise"]
        weight = voter["precision"] * 1.1 if matches else voter["precision"] * 0.7
        weight = min(1.0, round(weight, 2))
        
        # 85% agree, 15% disagree
        vote_value = 1 if random.random() < 0.85 else -1
        
        rationales_positive = [
            "Cross-referenced with official sources",
            "Verified from local knowledge",
            "Matches recent data",
            "Consistent with expert analysis",
        ]
        rationales_negative = [
            "Outdated information detected",
            "Contradicts recent reports",
            "Needs more context",
            "Partially misleading",
        ]
        
        votes.append({
            "user_id": voter["user_id"],
            "name": voter["name"],
            "location": voter["location"],
            "expertise": voter["expertise"],
            "vote": vote_value,
            "weight": weight,
            "rationale": random.choice(rationales_positive if vote_value == 1 else rationales_negative),
            "precision": voter["precision"],
        })

    
    return votes


def generate_demo_response(prompt: str) -> str:
    """Generate contextual AI response."""
    templates = [
        f"Based on analysis of multiple sources, this claim appears credible. Cross-referencing shows consistency with verified information.",
        f"Investigation reveals mixed evidence. The core assertion requires additional verification from authoritative sources.",
        f"This claim is well-supported by recent data. Multiple independent sources confirm the key details.",
    ]
    return random.choice(templates)



@app.post("/prompts", response_model=PromptResponse)
async def create_prompt(request: PromptRequest) -> PromptResponse:
    if not request.prompt.strip():
        raise HTTPException(status_code=422, detail="Prompt cannot be empty.")
    
    run_id = str(uuid.uuid4())
    
    provisional_answer = generate_demo_response(request.prompt)
    
    run_payload = {
        "run_id": run_id,
        "prompt": request.prompt,
        "requester": request.user_id or "anon",
        "status": "completed",
        "provisional_answer": provisional_answer,
        "confidence": None,
        "votes": [],
        "evidence": [
            {
                "tool_name": "google_search",
                "content": "Multiple sources reviewed. Key findings align with claim.",
            },
            {
                "tool_name": "web_crawler",
                "content": "Verified against primary sources and databases.",
            },
        ],
    }
    
    create_run(run_id, run_payload)
    enqueue_job(run_payload)
    
    return PromptResponse(**run_payload)


@app.get("/runs/{run_id}", response_model=PromptResponse)
async def get_run_status(run_id: str) -> PromptResponse:
    """Get run status and results."""
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")
    
    return PromptResponse(
        run_id=run["run_id"],
        status=run["status"],
        provisional_answer=run.get("provisional_answer"),
        confidence=run.get("confidence"),
        votes=run.get("votes", []),
        evidence=run.get("evidence", []),
    )


@app.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard() -> LeaderboardResponse:
    """Get top community reviewers."""
    entries = [
        LeaderboardEntry(
            user_id=user["user_id"],
            name=user["name"],
            precision=user["precision"],
            attempts=int(user["precision"] * 50),  # Demo calc
            points=int(user["precision"] * 1000),
            tier="Diamond" if user["precision"] > 0.85 else "Platinum" if user["precision"] > 0.75 else "Gold"
        )
        for user in sorted(DEMO_VOTERS, key=lambda x: x["precision"], reverse=True)
    ]
    return LeaderboardResponse(entries=entries)
