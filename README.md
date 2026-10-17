# ThreatWeaver

ThreatWeaver is a local security investigation workbench. Enter a bare domain (for example, `example.com`) or public IPv4 address, without `https://` or a path, to fetch live AlienVault OTX context, store sourced observations in FalkorDB, inspect bounded graph links, and get cautious next steps. The graph selects one observed passive DNS pivot for a follow-up lookup. Results separate observations, inferences, and unknowns. No blocking action is performed.

## Run locally

Prerequisites: Docker with Compose, Python 3.11–3.14, Node.js 20+, an OTX API key.

1. Copy `.env.example` to `.env` and set `OTX_API_KEY`. Keep the key private.
2. Start FalkorDB: `docker compose up -d`.
3. Install API packages: `python -m pip install -r backend/requirements.txt`.
4. Start the API from the repository root: `python -m uvicorn backend.app.main:app --reload --port 8000`.
5. In `frontend`, run `npm install`, then `npm run dev` (Windows PowerShell can use `npm.cmd`). Open `http://localhost:5173`.

If OTX is not configured, the UI reports that limitation and shows only already persisted graph evidence. The API health route at `http://localhost:8000/api/health` reports graph readiness and key configuration without exposing credentials. The optional DeepSeek planner requires `DEEPSEEK_API_KEY`; without it, the deterministic graph-guided route still runs and reports that the planner was not configured. Set `DEEPSEEK_MODEL=deepseek-flash` (the current default). The planner uses DeepSeek's Chat Completions API with thinking mode disabled for bounded tool calls.

## API and data model

- `POST /api/investigations` accepts `{"indicator":"example.com","expand":true,"use_agent":false}`.
- `GET /api/tools/lookup_indicator?indicator=example.com` fetches OTX and stores evidence.
- `GET /api/tools/trace_paths?indicator=example.com&depth=2&limit=30` returns at most two hops and 50 paths.
- `GET /api/tools/get_evidence?indicator=example.com&limit=30` returns stored source references.
- `GET /api/health` reports dependency state.
- `GET /api/investigations?limit=10` lists saved runs; `GET /api/investigations/{uuid}` restores a bounded result and its agent tool audit.
- `GET /api/observations/{id}` opens the provenance for any graph edge, including a second-hop edge.

The graph uses `Indicator`, `Observation`, `Evidence`, and `Investigation` nodes. `HAS_OBSERVATION` and `SUPPORTED_BY` attach source context; `POINTS_TO` and `OBSERVED_LINK` capture sourced passive DNS links. `HAS_INVESTIGATION` links saved run snapshots to their root indicator. Indicator keys are normalized as `domain:example.com` or `IPv4:8.8.8.8`. Deterministic hashes deduplicate observations and evidence across repeated fetches; `last_fetched_at` records refreshes. The query implementation uses parameters and fixed depth variants. The current response limits OTX passive DNS to 12 entries, pulses to 5 names, follow-up OTX lookups to one, graph depth to 2, and path/evidence results to 50. Saved snapshots have a 100 KB cap, and history queries return at most 20 runs.

The optional LLM planner can call three bounded tools. It may make at most three model iterations, three calls per iteration, and one OTX neighbor lookup. Only observed graph neighbors are eligible for that lookup. The deterministic report remains the source of displayed conclusions. The planner's status and audit count appear in the UI; its raw narrative is not presented as verified evidence.

OTX pulse membership and passive DNS association are context, not proof of malicious activity or compromise. Verify internal exposure and traffic before acting. A zero pulse count is just an OTX observation.

If the OTX passive DNS endpoint times out after the general endpoint succeeds, ThreatWeaver keeps the general findings and labels the result partial. Graph pivots require a successful passive DNS response. A `422` response means the submitted indicator failed validation; enter a bare domain or public IPv4 address.

## Verification and demo

Run `python -m pytest backend/tests` and `npm run build` in `frontend`. The test suite covers validation, OTX failures, graph bounds, deduplication inputs, and the no-compromise report language.

For a live demo, use `docs/DEMO.md`. This repository does not include a recorded video or a deployed service.
