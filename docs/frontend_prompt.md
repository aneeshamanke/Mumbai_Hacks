# Replit Prompt for Frontend Generation

```
You are building a lightweight social-style misinformation proof UI that connects to an existing FastAPI backend (see below). Requirements:

1. **Overall vibe**: playful "fact-check squad" dashboard, responsive, works on desktop + mobile. Think modern social feed with cards, badges, and live indicators.

2. **Pages/sections**
   - Hero input card with text area for the user to submit a prompt/question about a claim. Include CTA button "Analyze Claim".
   - Live status area showing:
       * Run ID and status pill (Queued / In Progress / Completed).
       * The agentic response text (fetched from backend `provisional_answer`).
       * Evidence chips for Gemini + Search (mock data is fine).
   - Crowd reaction panel displaying 3–5 reviewer avatars, expertise tags, and vote icons (thumbs up/down). Use dummy persona data but structure it so we can swap in real API data.
   - Leaderboard sidebar/table showing reviewer name, expertise, precision %, and badge tier.
   - Reward banner highlighting the gamification angle (points → goodies).

3. **Backend integration (must be plug‑and‑play)**
   - Base URL: assume same origin (the FastAPI backend runs on `http://localhost:8000`). Provide a single constant `API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000"` so we can override on deploy.
   - On submit, `POST ${API_BASE}/prompts` with JSON `{ "prompt": string }` → `{ run_id, status, provisional_answer, votes, confidence, evidence }`. Store the `run_id`.
   - Poll `GET ${API_BASE}/runs/{run_id}` every 3s until `status === "completed"`. Render:
       * `status` → badge (Queued/In Progress/Awaiting Votes/Completed).
       * `provisional_answer` → main text body.
       * `evidence[]` → chips showing `tool_name` + tooltip for `content`.
       * `votes[]` → avatar row (use `user_id` to map to a mock avatar), thumbs up/down from `vote`, tooltip with `rationale`, badge sized by `weight`.
       * `confidence` → progress bar.
   - Fetch leaderboard via `GET ${API_BASE}/leaderboard` → `{ entries: [...] }` and reuse the same data for the reward banner.
   - All API helpers live in `src/api.ts` (functions: `createPrompt(prompt)`, `pollRun(runId)`, `getLeaderboard()`); each returns mocked data if network fails so the UI still shows content.
   - Use `fetch`, handle JSON errors, and surface failures with a toast/snackbar.

4. **Implementation details**
   - Use plain React + Vite or Next.js (any Replit-supported stack). TypeScript preferred but JS ok.
   - Styling: TailwindCSS or a light component lib (e.g., Chakra). Include color-coded badges for statuses/tier.
   - Centralize API calls in a small `api.ts` helper and include mock fallbacks if endpoints fail (so the UI always shows something).
   - Keep components modular: `PromptForm`, `StatusCard`, `VotePanel`, `Leaderboard`.
   - Add loading skeletons/spinners for network calls.

5. **Demo mode**
   - Provide a "Run demo" button that triggers a fake prompt automatically to showcase the flow without typing.
   - Seed the crowd panel with dummy votes while polling so the page looks lively even before completion.

Deliverable: full frontend project ready to run on Replit (`npm install`, `npm run dev`). Include brief README with start instructions and `.env` note if needed.
```
