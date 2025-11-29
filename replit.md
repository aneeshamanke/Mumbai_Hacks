# VeriVerse - Misinformation Detection API

## Overview
VeriVerse is a FastAPI-based backend for a misinformation detection workflow. It provides endpoints for submitting claims/prompts for analysis, tracking analysis runs, and viewing a community reviewer leaderboard.

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
├── scripts/              # Utility scripts
│   └── data/state/      # Runtime state storage
├── data/
│   └── mock_users.json  # Demo reviewer profiles
├── config/
│   └── .env.example     # Environment template
└── docs/                 # Documentation
```

### API Endpoints
- `POST /prompts` - Submit a claim for analysis (returns run_id, AI response, empty votes)
- `GET /runs/{run_id}` - Get analysis status and results
- `GET /leaderboard` - Get top community reviewers

### Key Components
1. **API Gateway**: FastAPI server handling HTTP requests
2. **Orchestrator Worker**: Gemini AI agent with tool-calling capabilities
3. **Voting Service**: Simulates/handles community votes on responses
4. **Shared Storage**: JSON-backed persistence for runs and jobs

## Recent Changes
- **2025-11-29**: Removed auto-generated votes from POST /prompts
  - Claims now return with AI response but zero votes
  - Votes accumulate only when real users vote
  - Updated mock_users.json with consistent user profiles

## Environment Variables
- `GEMINI_API_KEY` - Google Gemini API key (required for AI features)
- `TAVILY_API_KEY` - Tavily API key (required for web search tools)
- `API_HOST` - Server host (default: 0.0.0.0)
- `API_PORT` - Server port (default: 5000)
- `LOG_DIR` - Log directory (default: ./logs)

## Running the Project
The API server runs automatically via the configured workflow:
```
python -m uvicorn api_gateway.main:app --host 0.0.0.0 --port 5000 --reload
```

## Testing Endpoints
```bash
# Submit a claim
curl -X POST http://localhost:5000/prompts \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Is the Earth flat?"}'

# Check run status
curl http://localhost:5000/runs/{run_id}

# Get leaderboard
curl http://localhost:5000/leaderboard
```
