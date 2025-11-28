# Misinformation Agentic Workflow (MVP Skeleton)

This repo scaffolds a 12-hour hackathon MVP where prompts run through a Gemini-powered agentic workflow, then crowd reviewers (dummy personas) vote on the response to build a weighted consensus, leaderboard, and reward loop.

## Repo Structure
```
.
├── api_gateway/            # FastAPI entrypoint (prompt intake, REST for frontend)
│   └── main.py
├── orchestrator/           # Gemini + tool orchestration worker
│   └── worker.py
├── voting_service/         # Handles reviewer selection + vote ingestion
│   └── worker.py
├── workers/                # Background workers (consensus, notifications)
│   └── consensus_worker.py
├── scripts/                # Cron-style scripts (mock data load, rewards)
│   ├── mock_data_loader.py
│   └── reward_cron.py
├── data/
│   └── mock_users.json     # Pre-seeded reviewer personas + stats
├── data/state/             # JSON-backed run store + queue (auto-created)

├── config/
│   └── .env.example        # Required env vars
├── docs/
│   └── architecture.md     # High-level architecture & flow
└── README.md
```

## MVP Flow
1. `api_gateway` receives prompt, creates `run_id`, persists metadata in `data/state/runs.json`, and enqueues work in `data/state/jobs.json`.
2. `orchestrator` pops jobs, calls Gemini Flash + search (mocked), stores artifacts, and updates run status/evidence.
3. `voting_service` detects `awaiting_votes` runs, simulates reviewer votes, and updates run confidence while waiting for manual overrides.
4. `workers/consensus_worker` demonstrates the scoring math used by `voting_service` (shared in `shared/consensus.py`).
5. `scripts/reward_cron.py` transforms vote history → leaderboard/rewards snapshots for the frontend.

## Getting Started
1. `cp config/.env.example .env` and fill in `GEMINI_API_KEY`, `MONGO_URI`, `REDIS_URL`.
2. (Optional) create & activate a virtualenv, then install dependencies once you flesh out each service.
3. Run `python scripts/mock_data_loader.py` to seed Mongo (or local JSON) with reviewer personas + stats.
4. Start services (separate terminals):  
   - `uvicorn api_gateway.main:app --reload`  
   - `python orchestrator/worker.py`  
   - `python voting_service/worker.py`
5. Trigger a prompt via `POST /prompts`, poll `/runs/{run_id}` to track status, and call `/leaderboard` for standings. Use `docs/frontend_prompt.md` to spin up the Replit frontend and point it at this backend.

## Frontend Integration Cheatsheet
- `POST /prompts` → `{ run_id, status }`
- `GET /runs/{run_id}` → `{ run_id, status, provisional_answer, confidence, votes[], evidence[] }`
- `GET /leaderboard` → `{ entries: [{ user_id, name, precision, attempts, points, tier }] }`
Run the FastAPI server (`localhost:8000`), point the Replit frontend's API client to the same origin (or configure proxy), and everything functions without extra glue code.

## Notes
- JSON-backed queue/state keeps services decoupled for the hackathon; swap with Redis/Mongo once ready.
- Frontend prompt + integration instructions live in `docs/frontend_prompt.md` for quick Replit generation.
