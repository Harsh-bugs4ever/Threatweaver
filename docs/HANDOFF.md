# ThreatWeaver implementation memory

ThreatWeaver is a hackathon MVP for security triage. Its primary workflow investigates a domain or IPv4 address with real AlienVault OTX data, stores observations and evidence in FalkorDB, and uses bounded graph paths to suggest the next investigation step. The graph is a required part of the reasoning loop, not merely a UI artifact.

The user asked to start building, break the work down, and give GPT Sol durable memory. This document and `BUILD_PLAN.md` carry that context across turns. All credentials come from environment variables. Never fabricate intelligence, compromise claims, live metrics, or a recorded demo. When OTX, OpenAI, or FalkorDB is unavailable, show the exact limitation and return honest results.

The hackathon runs October 15–18, 2026 and closes October 18 at 23:59 IST. Its security triage track and FalkorDB centrality make a local, demonstrable vertical slice the priority. Prepare local setup and a demo script. Recording and submission require a human.

Implementation decisions: Python FastAPI API, official FalkorDB Python client, React and TypeScript UI. OTX is the external source. The first version supports domain and IPv4 investigations, with per-source evidence IDs and timestamps, observation versus inference distinctions, safe parameterized queries and strict traversal/tool limits. No actual blocking action is performed.
