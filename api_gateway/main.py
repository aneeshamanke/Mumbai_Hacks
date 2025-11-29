"""FastAPI entrypoint for VeriVerse misinformation detection."""

from __future__ import annotations
import os
import uuid
import random
from typing import Any, Dict, List, Optional, Union
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.storage import create_run, enqueue_job, get_run, update_run
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "../config/.env"))

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
    user_id: Optional[str] = None


class Evidence(BaseModel):
    tool_name: str
    content: str





class Step(BaseModel):
    step: int
    thought: str
    tool: str
    tool_input: Union[Dict[str, Any], str]
    tool_output: str


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
    provisional_answer: Optional[str] = None
    confidence: Optional[float] = None
    votes: Optional[List[VotePayload]] = None
    evidence: Optional[List[Evidence]] = None
    citations: Optional[List[str]] = None
    steps: Optional[List[Step]] = None
    ground_truth: Optional[int] = None
    topics: Optional[List[str]] = None
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None


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


def extract_topics_from_prompt(prompt: str) -> List[str]:
    """Extract relevant topics from claim text for source matching.
    
    Uses keyword matching to identify claim categories.
    Returns list of topics that map to credible_sources.json categories.
    """
    prompt_lower = prompt.lower()
    topics = []
    
    topic_keywords = {
        "Technology": ["tech", "ai", "software", "app", "computer", "internet", "digital", "cyber", "startup"],
        "Finance": ["market", "stock", "finance", "economy", "rbi", "bank", "investment", "crypto", "bitcoin"],
        "Sports": ["sport", "game", "player", "team", "match", "tournament", "league"],
        "Sports/Cricket": ["cricket", "ipl", "bcci", "test match", "odi", "t20", "wicket", "batsman"],
        "Sports/Football": ["football", "soccer", "fifa", "premier league", "goal", "striker"],
        "Science/Health": ["health", "medical", "doctor", "hospital", "disease", "vaccine", "covid", "medicine"],
        "Science/General": ["science", "research", "study", "experiment", "discovery", "nasa", "space"],
        "News/India": ["india", "mumbai", "delhi", "bangalore", "modi", "parliament", "rupee"],
        "Government/India": ["government", "ministry", "pib", "policy", "law", "election"],
        "Environment": ["climate", "environment", "pollution", "carbon", "green", "wildlife"],
        "Aviation": ["flight", "airline", "airport", "aviation", "plane", "pilot"],
        "Fact-Checking": ["fake", "hoax", "rumor", "viral", "forward", "whatsapp"],
    }
    
    for topic, keywords in topic_keywords.items():
        if any(keyword in prompt_lower for keyword in keywords):
            topics.append(topic)
    
    if not topics:
        topics = ["General"]
    
    return topics



@app.post("/prompts", response_model=PromptResponse)
async def create_prompt(request: PromptRequest) -> PromptResponse:
    if not request.prompt.strip():
        raise HTTPException(status_code=422, detail="Prompt cannot be empty.")
    
    run_id = str(uuid.uuid4())
    
    # Initialize Worker
    from orchestrator.worker import OrchestratorWorker
    worker = OrchestratorWorker()
    
    # Create Job Payload
    job = {
        "run_id": run_id,
        "prompt": request.prompt,
    }
    
    # Run Agent Synchronously
    print(f"Processing request {run_id}: {request.prompt}")
    confidence = 0.0
    try:
        result = worker.run(job)
        final_answer = result["answer"]
        tool_outputs = result["tools"]
        confidence = result.get("confidence", 0.0)
        
        # Clean up final_answer to remove "Sources:" block
        import re
        source_pattern = r"\n+(\*\*|#+\s)?(Sources|References|Citations).*?(\Z)"
        final_answer = re.sub(source_pattern, "", final_answer, flags=re.DOTALL | re.IGNORECASE).strip()
    except Exception as e:
        print(f"Error running agent: {e}")
        final_answer = f"Error processing request: {str(e)}"
        tool_outputs = []
        confidence = 0.0

    # Map Tool Outputs to Evidence Format
    evidence = []
    for output in tool_outputs:
        evidence.append({
            "tool_name": output.get("tool_name", "unknown"),
            "content": output.get("content", "")
        })

    # Extract Sources (URLs only)
    import re
    sources = []
    # Old Markdown: r"- \*\*(.*?)\*\*\s+.*?\s+Source: (.*?)(?=\n\n|\Z)"
    # New Plain Text: Title: ...\nContent: ...\nSource: ...
    citation_pattern = r"Title: (.*?)\nContent: .*?\nSource: (.*?)(?=\n\n|\Z)"
    
    for output in tool_outputs:
        content = output.get("content", "")
        if output.get("tool_name") in ["web_search", "get_news"]:
            matches = re.finditer(citation_pattern, content, re.DOTALL)
            for match in matches:
                url = match.group(2).strip()
                if url not in sources:
                    sources.append(url)

    # Extract Steps
    steps = []
    for i, output in enumerate(tool_outputs):
        metadata = output.get("metadata", {})
        steps.append({
            "step": i + 1,
            "thought": metadata.get("thought", "No thought provided."),
            "tool": output.get("tool_name", "unknown"),
            "tool_input": metadata.get("args", {}),
            "tool_output": output.get("content", "")[:500] + "..." if len(output.get("content", "")) > 500 else output.get("content", "")
        })

    from datetime import datetime
    
    topics = extract_topics_from_prompt(request.prompt)
    
    run_payload = {
        "run_id": run_id,
        "prompt": request.prompt,
        "requester": request.user_id or "anon",
        "status": "completed",
        "provisional_answer": final_answer,
        "confidence": confidence,
        "votes": [],
        "evidence": evidence,
        "sources": sources,
        "steps": steps,
        "topics": topics,
        "created_at": datetime.now().isoformat(),
        "ground_truth": None,
        "resolved_at": None,
        "resolved_by": None,
    }
    
    # Persist run (optional, as worker already persists)
    create_run(run_id, run_payload)
    
    return PromptResponse(**run_payload)


@app.get("/runs/{run_id}", response_model=PromptResponse)
async def get_run_status(run_id: str) -> PromptResponse:
    """Get run status and results."""
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")
    
    # Ensure evidence is correctly formatted
    evidence_data = run.get("evidence", [])
    formatted_evidence = []
    if evidence_data:
        for item in evidence_data:
            if isinstance(item, dict):
                formatted_evidence.append(Evidence(
                    tool_name=item.get("tool_name", "unknown"),
                    content=item.get("content", "")
                ))
            else:
                # Handle legacy format if any
                formatted_evidence.append(Evidence(tool_name="unknown", content=str(item)))

    return PromptResponse(
        run_id=run["run_id"],
        status=run["status"],
        provisional_answer=run.get("provisional_answer"),
        confidence=run.get("confidence"),
        votes=run.get("votes", []),
        evidence=formatted_evidence,
        citations=run.get("citations", []),
        steps=run.get("steps", []),
        ground_truth=run.get("ground_truth"),
        topics=run.get("topics", []),
        resolved_at=run.get("resolved_at"),
        resolved_by=run.get("resolved_by"),
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


class ScoreResponse(BaseModel):
    scored: bool
    run_id: str
    ground_truth: Optional[int] = None
    correct_voters: List[str] = []
    incorrect_voters: List[str] = []


@app.post("/admin/score/{run_id}", response_model=ScoreResponse)
async def score_claim(run_id: str) -> ScoreResponse:
    """Awards points to voters after claim resolution.
    
    Compares each vote against ground_truth and categorizes voters.
    In production, this would call VeriVerse API to award points.
    """
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")
    
    ground_truth = run.get("ground_truth")
    if ground_truth is None:
        raise HTTPException(status_code=400, detail="Claim has not been resolved yet.")
    
    correct_voters = []
    incorrect_voters = []
    
    for vote in run.get("votes", []):
        user_id = vote.get("user_id")
        vote_value = vote.get("vote")
        
        if vote_value == ground_truth:
            correct_voters.append(user_id)
        else:
            incorrect_voters.append(user_id)
    
    return ScoreResponse(
        scored=True,
        run_id=run_id,
        ground_truth=ground_truth,
        correct_voters=correct_voters,
        incorrect_voters=incorrect_voters,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
