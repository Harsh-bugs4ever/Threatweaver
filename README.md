# ThreatWeaver

ThreatWeaver is a local security investigation workbench for a **domain or public IPv4 address**. It collects live external context, saves source-backed observations in FalkorDB, follows bounded graph links, and produces a report that separates observations, inferences, and unknowns.

An OTX pulse mention or DNS connection is a lead for investigation. It does **not** establish that an IP is malicious or that a machine is compromised. ThreatWeaver recommends next steps; it does not block traffic or isolate systems.

## Submission links and requirements

| Required item | Location / status |
| --- | --- |
| Public source-code repository | [Harsh-bugs4ever/Threatweaver](https://github.com/Harsh-bugs4ever/Threatweaver) — public access verified on October 18, 2026. |
| Setup instructions | [Run locally](#run-locally), including Windows and macOS/Linux commands, configuration, and health checks. |
| Graph data model | [Model and limits](#data-model-and-limits) and the [detailed graph-model reference](docs/GRAPH_MODEL.md). |
| Cypher queries / graph algorithms | [Query and algorithm guide](docs/GRAPH_QUERIES.md), [actual query templates](docs/queries.cypher), and [implementation](backend/app/graph.py). This project uses **Cypher with FalkorDB, not GraphQL**. |
| Working-project demo video | **Pending:** record and upload the four-minute demo, then place its accessible URL here and in [the submission sheet](docs/SUBMISSION.md). [Recording script](docs/DEMO.md). |
| Live deployment or complete local setup | **Local setup provided below.** No hosted deployment is claimed. The app requires the FastAPI service, outbound source access, and persistent FalkorDB; publishing the static frontend alone is insufficient. |
| Entered track | **Pending:** select the organizer's exact track name and enter it here and in [the submission sheet](docs/SUBMISSION.md). The project's focus is graph-backed security investigation; this is a description, not a confirmed track title. |

The code and documentation can be pushed now, but the submission checklist remains incomplete until the video URL and exact track are supplied. See [submission preparation](docs/SUBMISSION.md) for the remaining steps and a project description.

## Technology stack

React, TypeScript, and Vite provide the interface; React Flow renders relationship graphs. Python/FastAPI coordinates collection and reporting. FalkorDB stores the property graph and is queried with Cypher. Docker Compose runs local FalkorDB. Sources are AlienVault OTX and Google Public DNS; DeepSeek is an optional bounded tool planner. Explanatory diagrams are supplied as editable Excalidraw scenes with SVG previews.

## System flow

The website opens with a product overview at `/`, a searchable field guide at `/docs`, and the investigation workbench at `/investigate`. The guide covers setup, architecture, nodes and arrows, two-hop paths, evidence provenance, report interpretation, planner bounds, API routes, and troubleshooting.

The on-site diagrams include downloadable Excalidraw scenes and matching SVG previews in `frontend/public/diagrams`. Regenerate these together with `python docs/generate_web_diagrams.py`. Download a scene from the documentation and open it in Excalidraw to edit it for a presentation. For static hosting, configure an SPA fallback to `index.html` so `/docs` and `/investigate` can be opened directly; Vite's development and preview servers already provide this fallback.

![ThreatWeaver system flow](docs/system-flow.svg)

The diagram is also available as an [editable Excalidraw scene](docs/system-flow.excalidraw). Open that file in [Excalidraw](https://excalidraw.com/) to rearrange or export it. The SVG above is the README preview; both files use the same layout, with separate connector lanes and no crossing lines.

1. The React workbench sends a bare domain or public IPv4 address to FastAPI.
2. FastAPI validates the input. It requests OTX general intelligence and passive DNS. For domains, it also requests current A records from Google Public DNS. OTX passive DNS and current DNS are stored as different observation types.
3. FastAPI writes indicators, observations, source references, and investigation history to FalkorDB. It reads up to two hops of sourced links and may select one current observed neighbor for a follow-up OTX lookup.
4. The workbench displays the report, graph, evidence inspector, source warnings, and saved investigations. The optional DeepSeek planner can call bounded read tools and one observed-neighbor lookup; its calls are audited. The evidence-backed report remains authoritative.

## Run locally

You need Docker Desktop with Compose, Python 3.11–3.14, and Node.js 20+. An [AlienVault OTX key](https://otx.alienvault.com/) enables live threat intelligence. A DeepSeek API key is optional for the tool planner. Local FalkorDB requires no cloud account.

Run these commands from the repository root in PowerShell:

```powershell
git clone https://github.com/Harsh-bugs4ever/Threatweaver.git
cd Threatweaver
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

If you already cloned the repository, skip `git clone` and change to your existing checkout. Set `OTX_API_KEY` in `.env`. Set `DEEPSEEK_API_KEY` only if you want the optional planner. Keep both keys private; `.env` is ignored by Git. Python 3.11+ is required by the backend; the frontend requires Node.js 20+.

| Environment variable | Purpose / default |
| --- | --- |
| `OTX_API_KEY` | Required for live OTX context; without it, the report includes a missing-key warning. Current DNS can still be collected. |
| `DEEPSEEK_API_KEY` | Optional; only needed when enabling the tool planner. |
| `DEEPSEEK_MODEL` | Planner model, default `deepseek-flash`. |
| `FALKORDB_HOST`, `FALKORDB_PORT` | Database endpoint, defaults `localhost:6379`. |
| `FALKORDB_GRAPH` | Graph name, default `threatweaver`. |
| `CORS_ORIGINS` | Allowed browser origins; `.env.example` includes localhost and 127.0.0.1 on port 5173. |

The API process needs outbound HTTPS access to OTX and `dns.google`, plus `api.deepseek.com` when the planner is enabled. API keys stay on the backend; the React frontend does not receive them.

Start FalkorDB after Docker Desktop is running:

```powershell
docker compose up -d
docker compose ps
```

Create a Python virtual environment and start the API:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Leave that terminal open. In another PowerShell terminal, from the repository root, run:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open the [landing page](http://127.0.0.1:5173/), [documentation](http://127.0.0.1:5173/docs), or [investigation workbench](http://127.0.0.1:5173/investigate). The [API health page](http://127.0.0.1:8000/api/health) should show `"graph": "ready"`; it also reports whether the OTX and DeepSeek keys are configured without revealing them. Use a bare domain such as `example.com` or a public IPv4 address such as `8.8.8.8`—no `https://` or path.

For **macOS/Linux**, use the same cloned repository and `.env` variables. Run the following from its root (edit `.env` in your preferred editor before starting the API):

```bash
cp -n .env.example .env
docker compose up -d
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

In another terminal, from the repository root:

```bash
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Confirm the full path through the frontend proxy in PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:5173/api/health
```

On macOS/Linux, use `curl http://127.0.0.1:5173/api/health`. Expect `service: ready`, `graph: ready`, and `otx_configured: true` after configuring OTX. A missing DeepSeek key is acceptable when the planner is disabled. Run an investigation and inspect warnings to verify actual source access; configuration flags alone do not validate provider credentials or connectivity.

| Local address | Purpose |
| --- | --- |
| `http://localhost:5173` | ThreatWeaver website |
| `http://localhost:8000/api/health` | API and dependency status |
| `http://localhost:3000` | FalkorDB Browser |
| `localhost:6379` | FalkorDB database connection; not a web page |

Compose binds FalkorDB to localhost. Its named volume is mounted at the database's actual data directory, with append-only persistence enabled. Saved data survives container recreation. `docker compose down -v` removes the volume and its graph data.

## See the same graph in FalkorDB Browser

Run a domain investigation in ThreatWeaver. Open `http://localhost:3000`—or click **Open in FalkorDB** on the graph card—and select the `threatweaver` graph. This is the same database used by the website.

To inspect `example.com` links, run this read-only query in FalkorDB Browser:

```cypher
MATCH (d:Indicator {key: 'domain:example.com'})-[r:OBSERVED_LINK]-(ip:Indicator)
RETURN d.key, ip.key, r.predicate, r.observation_id
LIMIT 20
```

`current_dns_a` means a current Google Public DNS A answer. `passive_dns` means an OTX passive DNS association. Select an edge in ThreatWeaver to inspect the underlying observation ID, source URL, and timestamps. Current resolution can change, and shared infrastructure does not prove common ownership or malicious intent.

## Data model and limits

The workbench includes quick-fill example indicators, evidence search, and an exact source-ID filter. Download the current investigation as Markdown for review or JSON for its complete report, graph, evidence, and tool audit. Markdown exports retain source references, timestamps, and uncertainty statements.

Recommended actions have a progress checklist saved locally in this browser for each indicator. Reopening an indicator restores checks for matching action text; checklist progress is not shared with other browsers or included in exports. The evidence inspector supports keyboard navigation and closes with Escape.

The graph has `Indicator`, `Observation`, `Evidence`, and `Investigation` nodes. `HAS_OBSERVATION` and `SUPPORTED_BY` retain provenance; `POINTS_TO` and `OBSERVED_LINK` connect sourced indicators; `HAS_INVESTIGATION` retains a run. Repeated fetches reuse stable observation and evidence IDs and update the last fetch time.

| Node | Key properties | Role |
| --- | --- | --- |
| `Indicator` | `key`, `kind`, `value` | Domain or public IPv4; keys look like `domain:example.com` or `IPv4:8.8.8.8`. |
| `Observation` | `id`, `predicate`, `object`, `source_time`, `last_fetched_at` | Recorded finding, such as `current_dns_a`, `passive_dns`, or `otx_pulse_count`. |
| `Evidence` | `id`, `source_id`, `url`, `last_fetched_at` | Source reference supporting an observation. |
| `Investigation` | `id`, `indicator`, `created_at`, `status`, `method`, `snapshot` | Saved JSON result and tool audit for one run. |

```text
Indicator --HAS_OBSERVATION--> Observation --SUPPORTED_BY--> Evidence
                                  |
                               POINTS_TO
                                  v
Indicator --OBSERVED_LINK----> Related Indicator
    |
HAS_INVESTIGATION
    v
Investigation
```

`OBSERVED_LINK` stores `predicate` and `observation_id`. Graph paths traverse this relationship in either direction; the arrow does not indicate attack traffic. The full [graph-model reference](docs/GRAPH_MODEL.md) explains identity, deduplication, timestamps, and snapshots. The [query guide](docs/GRAPH_QUERIES.md) explains how stored relationships determine the follow-up lookup.

Queries use fixed Cypher templates with parameters. The current limits are: two graph hops, 50 paths or evidence records per query (30 in the main investigation), 12 OTX passive DNS entries, five current DNS A answers, one deterministic follow-up OTX lookup, and 20 recent investigations (eight in the sidebar). The optional planner separately allows at most three model iterations, three tool calls per iteration, and one observed-neighbor lookup in its own stage. It cannot issue arbitrary Cypher or production blocking actions.

Useful API routes:

| Route | Purpose |
| --- | --- |
| `POST /api/investigations` | Run an investigation; accepts `{"indicator":"example.com","expand":true,"use_agent":false}` |
| `GET /api/investigations?limit=10` | List saved runs |
| `GET /api/investigations/{uuid}` | Reopen a saved run and tool audit |
| `GET /api/tools/trace_paths?indicator=example.com&depth=2&limit=30` | Inspect bounded graph paths |
| `GET /api/tools/get_evidence?indicator=example.com&limit=30` | Inspect source references |
| `GET /api/observations/{id}` | Inspect evidence behind a graph edge |

## Troubleshooting

| Symptom | Check |
| --- | --- |
| FalkorDB Browser does not open | Use `http://localhost:3000`, not port `6379`. Check `docker compose ps`. |
| API health reports `graph: unavailable` | Start Docker Desktop, run `docker compose up -d`, then check `docker compose logs falkordb`. |
| Investigation returns `422` | Enter a bare domain or public IPv4 address. Local/private IPs and full URLs are unsupported. |
| OTX result is partial | OTX passive DNS may time out. General OTX findings and current DNS links are retained when available; the warning names the failed source. |
| OTX or DeepSeek says key missing | Add the key to `.env` and restart the backend. |
| DNS and OTX report `ConnectError` | Ensure the API process has outbound HTTPS access. Network restrictions on the API can differ from your browser's access. |
| Port 5173 or 8000 is already in use | Stop the previous project server, then restart it. The documented frontend command refuses to silently choose a different port. |
| No second-hop path appears | A second hop requires stored links beyond the immediate neighbor. Enable the pivot if appropriate; a sparse graph is a valid result. |

Stop the frontend and API with `Ctrl+C` in their terminals. Use `docker compose stop` to stop FalkorDB while keeping its stored graph.

## Verify and demo

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
cd frontend
npm.cmd run build
```

The tests use mocked source responses and check validation, partial OTX results, current DNS normalization, graph bounds, and evidence language. They do not certify live provider availability. For a four-minute walkthrough and recording checklist, follow [the demo script](docs/DEMO.md). No hosted service or recorded video is claimed until real links are supplied in the submission table above.
