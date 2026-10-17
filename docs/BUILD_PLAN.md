# Build plan

1. **Foundation** — scaffold API and UI, environment sample, Docker Compose and setup documentation. Status: complete.
2. **Investigation** — validate indicators; fetch real OTX data; persist deduplicated entities, observations, evidence, investigation snapshots and tool audits in FalkorDB; expose bounded lookup, paths and evidence tools; make graph relationships influence investigation priority. Status: implemented; live FalkorDB and OTX integration pending an available Docker daemon and API key.
3. **Workbench** — build a responsive investigation UI with graph, findings, recommendations, evidence inspector, saved history, loading and useful failures. Status: complete and production build verified.
4. **Validation and delivery** — meaningful API tests, UI build, local integration when services and credentials permit, and a reproducible demo script. Status: tests and build complete; live integration and recorded video pending runnable external services and human recording.

Scope guardrails: no unsupported compromise language, no invented counts or data, no unbounded graph traversal, no real blocking, and no claims of successful external API calls without evidence.
