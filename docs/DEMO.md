# Live demo script

1. Start FalkorDB, API, and frontend as described in the README. Check `/api/health` for `graph: ready` and `otx_configured: true`.
2. Enter a domain or public IPv4 address you are authorized to investigate. Show the OTX pulse count and bounded passive DNS links. Data will vary with the chosen indicator and OTX at demo time.
3. Click a graph edge to inspect its observation ID, source ID, source timestamp, and OTX URL. Open the Evidence tab to see stored references.
4. Explain that the graph selects at most one pivot from links returned in the current OTX fetch. Show its lookup status and any partial error.
5. Re-run the same indicator to show deduplicated graph observations and updated fetch times. Demonstrate an invalid address and the missing-key message if helpful.
6. Optionally enable the LLM planner when a DeepSeek key is configured, then show its audited call count. Its text is not treated as verified evidence.

Record the real running UI if a submission video is required. Do not use fabricated findings or describe an unrecorded video as complete.
