# Architecture Overview

## High-Level Flow
1. **Prompt intake (API Gateway)**  
   - Receives prompt, authenticates the requester, logs consent & metadata.  
   - Writes a `run` record in the JSON state store (`data/state/runs.json`) and enqueues a job (`jobs.json`).  
   - Provides REST polling endpoint `/runs/{run_id}` consumed by the frontend; swap with SSE later if desired.

2. **Agent Orchestrator**  
   - Pops jobs, selects tools (Gemini Flash, mock web search, other utilities).  
   - Captures tool outputs, normalizes evidence, and stores them under `runs/<run_id>/artifacts`.  
   - Emits structured logs (`run_id`, latency, tool decisions) for traceability and posts provisional answer back to API Gateway.

3. **Voting Service**  
   - Triggers once the orchestrator posts an answer.  
   - Fetches relevant reviewer personas (dummy data in MVP) using expertise + location similarity.  
   - Simulates votes or accepts real user votes, persisting them in the `votes` collection with weight components.

4. **Consensus Worker**  
   - Runs whenever a vote arrives or on timeout.  
   - Calculates weighted confidence: `score = Σ(weight_i * vote_i)` using precision, relevance, and recency.  
   - Updates `run_results` with confidence, verdict, and supporting evidence; notifies frontend.

5. **Rewards & Leaderboard Cron**  
   - Hourly batch job scans votes to recompute per-user precision, attempts, and reward points.  
   - Publishes leaderboard snapshots to MongoDB and exposes them via `/leaderboard`.

## Services
- **frontend/** (not included here) consumes API and displays prompt form, response, votes, leaderboard.
- **api_gateway/** receives HTTPS traffic, validates requests, and exposes REST/WebSocket endpoints.
- **orchestrator/** handles tool calling via Google AI SDK + Gemini Flash key.
- **voting_service/** ingests votes (simulated or real) and enforces anti-spam throttles.
- **workers/consensus_worker.py** recalculates confidence asynchronously.
- **scripts/** holds cron-style jobs (reward recalculation, mock data seeding).

## Data Stores
- **MongoDB collections**
  - `users`: profile, expertise vector, consent version, precision stats.
  - `runs`: prompt metadata, tool input/output, timestamps.
  - `votes`: individual vote payloads plus weight components.
  - `run_results`: final verdict snapshots + audit trail.
  - `leaderboard`: cached leaderboard rows.
  - `rewards`: mapping of user → reward status.
  - `sessions`: auth + anti-spam fingerprints.

## Messaging & Telemetry
- **JSON-backed queue/state** for the hackathon (upgrade to Redis/Cloud Tasks when ready).
- **Redis pub/sub or Mongo change streams** (future) for propagating vote updates.
- **Structured logging** (JSONL) per service for easy walkthroughs during the demo.

## Secrets & Config
- `.env`/Secret Manager for Gemini API key, Mongo URI, Redis URL, and JWT secret.
- Local development uses `.env.example` to scaffold required variables.

## MVP Assumptions
- Reviewer personas + vote histories are pre-seeded from `data/mock_users.json`.
- Voting can be auto-simulated while still exposing REST endpoints to demonstrate manual overrides.
- Rewards are non-monetary badges calculated by `scripts/reward_cron.py`.
