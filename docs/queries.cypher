// ThreatWeaver: actual Cypher templates extracted from backend/app/graph.py.
// Regenerate: python docs/export_cypher.py
// Includes writes and reads. Execute one template with its parameters, not the whole file.
// Algorithm explanation and literal read-only demo queries: docs/GRAPH_QUERIES.md.

// initialize — backend/app/graph.py:33
// Parameters: none
CREATE INDEX FOR (i:Indicator) ON (i.key);

// initialize — backend/app/graph.py:34
// Parameters: none
CREATE INDEX FOR (e:Evidence) ON (e.id);

// initialize — backend/app/graph.py:35
// Parameters: none
CREATE INDEX FOR (o:Observation) ON (o.id);

// initialize — backend/app/graph.py:36
// Parameters: none
CREATE INDEX FOR (run:Investigation) ON (run.id);

// upsert_indicator — backend/app/graph.py:46
// Parameters: key, kind, value
MERGE (i:Indicator {key: $key}) SET i.kind=$kind, i.value=$value;

// add_observation — backend/app/graph.py:61
// Parameters: eid, fetched_at, kind, object, oid, predicate, source_id, source_time, subject, url, value
MERGE (s:Indicator {key:$subject}) SET s.kind=$kind, s.value=$value
MERGE (o:Observation {id:$oid}) SET o.predicate=$predicate, o.object=$object,
    o.source_time=$source_time, o.last_fetched_at=$fetched_at
MERGE (e:Evidence {id:$eid}) SET e.source_id=$source_id, e.url=$url,
    e.last_fetched_at=$fetched_at
MERGE (s)-[:HAS_OBSERVATION]->(o)
MERGE (o)-[:SUPPORTED_BY]->(e);

// add_observation — backend/app/graph.py:71
// Parameters: neighbor, neighbor_kind, neighbor_value, oid, predicate, subject
MATCH (s:Indicator {key:$subject}), (o:Observation {id:$oid})
MERGE (n:Indicator {key:$neighbor}) SET n.kind=$neighbor_kind, n.value=$neighbor_value
MERGE (o)-[:POINTS_TO]->(n)
MERGE (s)-[r:OBSERVED_LINK {observation_id:$oid}]->(n)
SET r.predicate=$predicate;

// get_evidence — backend/app/graph.py:81
// Parameters: key, limit
MATCH (i:Indicator {key:$key})-[:HAS_OBSERVATION]->(o:Observation)-[:SUPPORTED_BY]->(e:Evidence)
OPTIONAL MATCH (o)-[:POINTS_TO]->(n:Indicator)
RETURN o.id, o.predicate, o.object, o.source_time, o.last_fetched_at,
       e.id, e.source_id, e.url, n.key
ORDER BY o.last_fetched_at DESC LIMIT $limit;

// trace_paths — backend/app/graph.py:95
// Parameters: key, limit
MATCH (root:Indicator {key:$key})-[r:OBSERVED_LINK]-(n:Indicator)
RETURN root.key, n.key, r.observation_id, r.predicate LIMIT $limit;

// trace_paths — backend/app/graph.py:103
// Parameters: key, limit
MATCH (root:Indicator {key:$key})-[r1:OBSERVED_LINK]-(mid:Indicator)
      -[r2:OBSERVED_LINK]-(n:Indicator)
WHERE n.key <> root.key
RETURN root.key, mid.key, n.key, r1.observation_id, r2.observation_id,
       r1.predicate, r2.predicate
LIMIT $limit;

// recent_neighbors — backend/app/graph.py:132
// Parameters: key, limit
MATCH (i:Indicator {key:$key})-[:OBSERVED_LINK]-(n:Indicator)
RETURN DISTINCT n.key LIMIT $limit;

// save_investigation — backend/app/graph.py:143
// Parameters: created_at, id, key, method, snapshot, status
MATCH (i:Indicator {key:$key})
CREATE (run:Investigation {id:$id, indicator:$key, created_at:$created_at,
       status:$status, method:$method, snapshot:$snapshot})
CREATE (i)-[:HAS_INVESTIGATION]->(run);

// list_investigations — backend/app/graph.py:153
// Parameters: limit
MATCH (run:Investigation)
RETURN run.id, run.indicator, run.created_at, run.status, run.method
ORDER BY run.created_at DESC LIMIT $limit;

// get_investigation — backend/app/graph.py:161
// Parameters: id
MATCH (run:Investigation {id:$id}) RETURN run.snapshot LIMIT 1;

// get_observation — backend/app/graph.py:165
// Parameters: id
MATCH (o:Observation {id:$id})-[:SUPPORTED_BY]->(e:Evidence)
OPTIONAL MATCH (o)-[:POINTS_TO]->(n:Indicator)
RETURN o.id, o.predicate, o.object, o.source_time, o.last_fetched_at,
       e.id, e.source_id, e.url, n.key LIMIT 1;
