# VeriVerse - Misinformation Detection API

## Overview
VeriVerse is a FastAPI-based backend for a misinformation detection workflow. It provides endpoints for submitting claims/prompts for analysis, tracking analysis runs, viewing a community reviewer leaderboard, and automated claim resolution.

## Project Architecture

### Directory Structure
```
.
├── api_gateway/          # FastAPI REST API
│   └── main.py          # Main API endpoints
├── orchestrator/         # Gemini AI + tool orchestration worker
│   └── worker.py        # AI agent with search/weather/stock tools
├── voting_service/       # Handles reviewer votes
│   └── worker.py        # Vote simulation service
├── workers/              # Background workers
│   └── consensus_worker.py
├── shared/               # Shared utilities
│   ├── storage.py       # JSON-file backed storage
│   ├── tools.py         # AI tools (Tavily, weather, stocks, etc.)
│   └── consensus.py     # Vote confidence calculation
├── data/
│   ├── mock_users.json       # Demo reviewer profiles
│   └── credible_sources.json # Trusted source registry by category
├── resolution_worker.py  # Automated moderator resolution worker
├── config/
│   └── .env.example     # Environment template
└── docs/                 # Documentation
```

### API Endpoints
- `POST /prompts` - Submit a claim for analysis (returns run_id, AI response, topics, empty votes)
- `GET /runs/{run_id}` - Get analysis status, results, ground_truth, and resolution info
- `GET /leaderboard` - Get top community reviewers
- `POST /admin/score/{run_id}` - Score voters after claim resolution (awards points)

### Key Components
1. **API Gateway**: FastAPI server handling HTTP requests
2. **Orchestrator Worker**: Gemini AI agent with tool-calling capabilities
3. **Voting Service**: Simulates/handles community votes on responses
4. **Resolution Worker**: Automated moderator that verifies claims using credible sources
5. **Shared Storage**: JSON-backed persistence for runs and jobs

## Automated Resolution System

### How It Works
1. Claims older than 1 hour are checked by the resolution worker
2. Topics are extracted from claim text (Technology, Finance, Sports, etc.)
3. Credible sources are searched based on topic mapping
4. Verdict is determined: TRUE (1), FALSE (-1), or UNVERIFIABLE (null)
5. Resolved claims update with ground_truth, resolved_at, resolved_by

### Starting the Resolution Worker
```bash
python resolution_worker.py &
```
The worker runs hourly, checking pending claims and resolving them against credible sources.

### Credible Sources Registry
Located at `data/credible_sources.json`, maps topics to trusted domains:
- News/General: reuters.com, apnews.com, bbc.com
- Fact-Checking: snopes.com, factcheck.org, altnews.in
- Science/Health: who.int, cdc.gov, nih.gov
- And more...

## Recent Changes
- **2025-11-29**: Added automated moderator resolution system
  - Created credible_sources.json with trusted source registry
  - Added resolution_worker.py for hourly claim verification
  - Added topics extraction from prompts
  - Added ground_truth, resolved_at, resolved_by fields
  - Added /admin/score/{run_id} endpoint for scoring voters
- **2025-11-29**: Removed auto-generated votes from POST /prompts
  - Claims now return with AI response but zero votes
  - Votes accumulate only when real users vote

## Environment Variables
- `GEMINI_API_KEY` - Google Gemini API key (required for AI features)
- `TAVILY_API_KEY` - Tavily API key (required for web search and resolution)
- `API_HOST` - Server host (default: 0.0.0.0)
- `API_PORT` - Server port (default: 5000)
- `LOG_DIR` - Log directory (default: ./logs)

## Running the Project

### API Server (runs automatically via workflow)
```
python -m uvicorn api_gateway.main:app --host 0.0.0.0 --port 5000 --reload
```

### Resolution Worker (optional background process)
```
python resolution_worker.py &
```

## Testing Endpoints
```bash
# Submit a claim
curl -X POST http://localhost:5000/prompts \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Is the Earth flat?"}'

# Check run status (includes ground_truth if resolved)
curl http://localhost:5000/runs/{run_id}

# Get leaderboard
curl http://localhost:5000/leaderboard

# Score voters after resolution
curl -X POST http://localhost:5000/admin/score/{run_id}
```

## Response Fields
- `run_id`: Unique identifier for the claim
- `status`: completed, verified
- `provisional_answer`: AI-generated analysis
- `topics`: Extracted topics from claim
- `ground_truth`: 1 (TRUE), -1 (FALSE), null (unresolved)
- `resolved_at`: ISO timestamp when resolved
- `resolved_by`: "moderator_agent" for automated resolution
