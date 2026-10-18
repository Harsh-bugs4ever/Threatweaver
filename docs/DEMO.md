# Four-minute demo script

Record the real running project. Target 4 minutes; trim lookup waiting time if necessary. External data varies, so describe only the findings that appear. A script is not a completed demo video: upload the recording and place its accessible link in README.md and SUBMISSION.md.

## Before recording

- Start the database, API, and frontend using the README. Check `/api/health` for `graph: ready` and OTX configuration. Ensure the API can reach the external providers.
- Prepare tabs for the landing page, workbench, documentation, and FalkorDB Browser.
- Check Tripcraft once before recording to identify a genuine two-hop path if one exists. During the video, run the investigation once. Do not promise a second hop when no supporting stored relationships exist.
- In FalkorDB Browser, select `threatweaver`. Prepare the read-only demo queries from GRAPH_QUERIES.md.

## 0:00–0:35 — Problem and solution

[Show the landing page.]

“Hello everyone. This is ThreatWeaver, an evidence-first security investigation workbench.

When investigating an unfamiliar domain or IP address, analysts often switch between threat intelligence sources, DNS records, and investigation notes. The challenge is understanding how these findings connect while preserving their sources and timestamps.

ThreatWeaver brings that workflow into one place. It collects external context, connects related indicators through a graph, and produces a report separating observations, inferences, and unknowns.”

## 0:35–1:10 — Technology and architecture

[Show the architecture flowchart.]

“The frontend uses React and TypeScript, with React Flow for graph visualization. The backend uses Python and FastAPI.

AlienVault OTX provides pulse context and passive DNS, while Google Public DNS provides current domain A records.

FalkorDB stores the indicators, observations, source evidence, and investigation history. I query this graph using Cypher, not GraphQL.

The backend validates the input, collects source data, saves it, and reads bounded graph relationships. An optional DeepSeek planner supports audited tool calls.”

## 1:10–1:35 — Run Tripcraft

[Open /investigate. Enter tripcraft-blue.vercel.app. Enable the graph pivot, leave DeepSeek off, and click Investigate once.]

“I’ll demonstrate this using Tripcraft’s hostname.

The sidebar shows database readiness and whether the OTX key is configured. The graph pivot option allows one currently observed neighbor to receive an additional OTX lookup.

While collection runs, an important distinction: ThreatWeaver investigates external intelligence and infrastructure relationships. It does not scan the website for application vulnerabilities.”

## 1:35–2:05 — Website dashboard

[Show the result and summary cards.]

“The dashboard summarizes OTX pulses, graph links, evidence items, and the selected pivot.

These describe the available evidence; they are not risk scores. Zero OTX pulses does not prove that a website is safe.

The graph shows the starting indicator and its sourced relationships. Labels distinguish current DNS from historical passive DNS.

Selecting a connection opens its observation, source URL, and timestamps. The report below explains what was observed, what remains uncertain, and recommended next steps.”

[If partial, briefly explain the displayed source warning.]

## 2:05–2:45 — FalkorDB dashboard

[Switch to the prepared database graph.]

“This is the underlying FalkorDB graph.

Indicator nodes represent domains or public IPs. Observation nodes contain findings. Evidence nodes preserve source references, and Investigation nodes store saved runs.

The arrows explain their relationships. HAS_OBSERVATION connects an indicator to a finding. SUPPORTED_BY connects that finding to evidence. POINTS_TO identifies a related indicator.

OBSERVED_LINK directly connects two indicators through a sourced observation, while HAS_INVESTIGATION links an indicator to saved history.

The displayed node numbers are database identifiers, not threat scores.”

## 2:45–3:10 — Evidence and exports

[Return to the website. Open Evidence, select a row, then close it. Download Markdown.]

“The evidence ledger supports searching and source filtering. Each record exposes its provenance and available timestamps.

A recent retrieval does not necessarily mean the underlying observation is recent.

I can download a readable Markdown report, or export JSON containing the complete investigation response, including graph data and evidence.”

## 3:10–3:40 — Two-hop paths

[Show an actual two-hop path, or the documentation diagram explicitly as an illustration.]

“One hop crosses one relationship between indicators. For example, Tripcraft’s domain connects to a DNS-observed IP address.

A second hop can connect that IP to another domain through another stored relationship.

This surfaces investigation leads beyond the starting indicator while keeping traversal bounded to two hops.

A second hop appears only when supporting links exist. Shared hosting does not prove shared ownership or malicious activity.”

## 3:40–4:00 — Features and closing

[Briefly show the checklist, recent history, and documentation.]

“Other features include locally saved action checklists, investigation history, an optional audited planner, and searchable documentation with editable Excalidraw diagrams.

ThreatWeaver helps analysts trace connections back to evidence and choose their next investigation step. It supports informed review without treating associations as proof of compromise.

Thank you.”
