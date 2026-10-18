# ThreatWeaver submission sheet

## Links and selected track

| Field | Value |
| --- | --- |
| Project name | ThreatWeaver |
| Public repository | https://github.com/Harsh-bugs4ever/Threatweaver |
| Demo video | **Pending: paste the actual uploaded recording URL here and in README.md.** |
| Exact entered track | **Pending: select a track from the organizer's submission form and copy its exact name here and into README.md.** |
| Live deployment | Not provided; complete local setup is the chosen delivery option. Localhost URLs are not public deployment links. |
| Setup | [README: Run locally](../README.md#run-locally) |
| Graph data model | [GRAPH_MODEL.md](GRAPH_MODEL.md) |
| Cypher / algorithms | [GRAPH_QUERIES.md](GRAPH_QUERIES.md), [queries.cypher](queries.cypher), [graph.py](../backend/app/graph.py) |
| Four-minute recording script | [DEMO.md](DEMO.md) |

Repository public visibility was checked through GitHub's unauthenticated API on October 18, 2026. This does not establish that unpushed local changes are on the remote; push the final changes and inspect the repository before submitting.

## Project description for the submission form

ThreatWeaver is an evidence-first security investigation workbench for domains and public IPv4 addresses. It combines AlienVault OTX context and Google Public DNS observations, stores source-backed findings in FalkorDB, and uses parameterized Cypher queries to explore bounded one- and two-hop indicator relationships. Graph neighbors intersected with current source responses determine an optional follow-up lookup. The React dashboard exposes provenance, timestamps, uncertainty, saved investigations, action checklists, and Markdown/JSON exports. An optional DeepSeek planner uses restricted, audited tools. The product recommends next steps without treating graph associations as proof of compromise or performing automatic blocking.

Technology: React, TypeScript, Vite, React Flow, Python, FastAPI, FalkorDB, Cypher, Docker Compose, AlienVault OTX, Google Public DNS, optional DeepSeek. Editable explanatory diagrams are supplied as Excalidraw scenes.

## Requirements audit

- [x] Public source-code repository exists.
- [x] README contains portable setup instructions, environment configuration, health checks, and graph data model.
- [x] Actual Cypher templates and graph-algorithm explanations are included.
- [x] Complete local setup is supplied as the alternative to a hosted deployment.
- [ ] A working-project video is recorded, uploaded, accessible to judges, and linked from the README.
- [ ] The exact entered track is selected and stated in the README and submission form.
- [ ] Final changes are pushed to the public repository and the remote files are checked.

## Before submitting

1. Follow [the four-minute script](DEMO.md) and record the real running UI. Trim only waiting time if needed; do not replace findings with fabricated results.
2. Upload the recording to your chosen video host. Make it viewable by anyone with the link (or public), and verify access while signed out. Add its URL to this file and the README. An unrecorded script does not meet the demo-video requirement.
3. Select the organizer's exact track name. The repository's security-investigation focus is not a confirmed entry category.
4. From the repository root, run the backend tests and frontend build using the commands in the README. Review `git diff` and `git status`; `.env`, `.venv`, `node_modules`, and generated builds are ignored. Confirm that real credentials are not in staged files.
5. Commit and push the reviewed files. Open the public repository to verify the README, model guide, query export, diagrams, and video link are present on the branch you submit.
6. Submit the public repository URL, actual demo-video URL, selected track, and the README local-setup link. Do not submit a `localhost` address as a hosted deployment.
