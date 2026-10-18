# Cypher queries and graph algorithms

ThreatWeaver uses **FalkorDB and Cypher**, not GraphQL. Its graph logic is implemented in [`GraphStore`](../backend/app/graph.py), [`investigate`](../backend/app/investigation.py), and the [optional planner](../backend/app/agent.py).

The complete, parameterized query templates are exported to [`queries.cypher`](queries.cypher). Regenerate the export from the Python implementation with:

```bash
python docs/export_cypher.py
```

This export includes both read and write operations. Execute individual templates with the indicated parameters through a database client; it is a reference file, not a migration to run wholesale. Literal, read-only examples for FalkorDB Browser appear below.

## 1. Persist sourced observations

`GraphStore.add_observation` merges the subject indicator, stable observation, and stable evidence reference; it connects them with `HAS_OBSERVATION` and `SUPPORTED_BY`. Relational findings additionally merge the neighboring indicator and create `POINTS_TO` and `OBSERVED_LINK`. The direct link stores its predicate and observation ID.

All untrusted values are passed as query parameters. [`GRAPH_MODEL.md`](GRAPH_MODEL.md) documents identity and timestamps. Stable IDs and `MERGE` reuse matching observations across repeat fetches.

## 2. Read bounded one- and two-hop paths

The first query reads immediate neighbors:

```cypher
MATCH (root:Indicator {key:$key})-[r:OBSERVED_LINK]-(n:Indicator)
RETURN root.key, n.key, r.observation_id, r.predicate LIMIT $limit
```

If depth is two and the first result has not consumed the path budget, the second query reads two-link paths:

```cypher
MATCH (root:Indicator {key:$key})-[r1:OBSERVED_LINK]-(mid:Indicator)
      -[r2:OBSERVED_LINK]-(n:Indicator)
WHERE n.key <> root.key
RETURN root.key, mid.key, n.key, r1.observation_id, r2.observation_id,
       r1.predicate, r2.predicate
LIMIT $limit
```

The second query's `$limit` is the remaining path budget. Depth is clamped to one or two and the total path budget to 1–50; the main investigator requests 30 paths. If first-hop paths fill the budget, no second-hop query is run. Return ordering is not a ranking or an exhaustive discovery guarantee.

The application collects indicator keys from these paths and deduplicates displayed connections by observation ID. `truncated` is set when the returned path count reaches the budget; this conservatively signals a possible limit hit, not proof that additional paths exist. The website arranges nodes for readability; their screen positions carry no analytical meaning.

## 3. Let graph neighbors determine the follow-up

The deterministic investigator performs this bounded procedure:

1. Collect and persist root OTX findings; for domains, also collect current A answers.
2. Build `current_keys` from valid neighbors observed in those current source responses. A passive-DNS response can still describe historical associations.
3. If expansion is enabled and `current_keys` is nonempty, read up to ten graph neighbors using `recent_neighbors`. Despite its name, the query does not sort by recency or risk.
4. Filter the returned graph neighbors to `current_keys`; select at most the first eligible neighbor.
5. Perform one OTX lookup for that neighbor and persist its available observations.
6. Read the root's bounded graph paths and evidence, assemble the report, and save a run snapshot.

This makes the stored graph an input to the follow-up decision. It excludes stale-only neighbors from the current pivot and does not invent connections or recursively crawl newly discovered neighbors. The main stage makes at most one follow-up lookup, not one per hop.

The optional planner has its own separate allowance: up to three iterations, three calls per iteration, and one allowed-neighbor lookup within that stage. It uses fixed tools, cannot issue arbitrary Cypher, and does not replace the sourced report.

## 4. Retrieve provenance

`get_evidence` reads `Indicator → HAS_OBSERVATION → Observation → SUPPORTED_BY → Evidence` and optionally follows `POINTS_TO`. It orders records by last fetched time and clamps output to 50 records (30 in the main report). `get_observation` exposes the same provenance for a clicked graph connection. These queries let the analyst check why a link exists.

## 5. Store and reopen investigations

`save_investigation` creates a UUID run linked to the root. `list_investigations` returns up to 20 snapshots' metadata ordered by creation time. `get_investigation` reads the saved JSON snapshot rather than silently refreshing external data. The UI sidebar requests eight entries.

## Read-only demo queries

Open `http://127.0.0.1:3000`, select the `threatweaver` graph, and run the queries separately after a Tripcraft investigation. Results depend on the stored observations.

### Direct Tripcraft connections

```cypher
MATCH (root:Indicator {key:'domain:tripcraft-blue.vercel.app'})-[r:OBSERVED_LINK]-(n:Indicator)
RETURN root, r, n
LIMIT 30
```

### Genuine two-hop indicator paths

```cypher
MATCH (root:Indicator {key:'domain:tripcraft-blue.vercel.app'})-[r1:OBSERVED_LINK]-(mid:Indicator)
      -[r2:OBSERVED_LINK]-(n:Indicator)
WHERE n.key <> root.key
RETURN root, r1, mid, r2, n
LIMIT 30
```

### Findings and supporting sources

```cypher
MATCH (root:Indicator {key:'domain:tripcraft-blue.vercel.app'})-[h:HAS_OBSERVATION]->(o:Observation)
      -[s:SUPPORTED_BY]->(e:Evidence)
RETURN root, h, o, s, e
LIMIT 30
```

### Current answers versus historical associations

```cypher
MATCH (root:Indicator {key:'domain:tripcraft-blue.vercel.app'})-[r:OBSERVED_LINK]-(n:Indicator)
RETURN n.key, r.predicate, r.observation_id
LIMIT 30
```

Inspect `current_dns_a` and `passive_dns` separately. Two-hop paths and shared IPs are investigation leads, not threat verdicts.
