import hashlib
import json
from uuid import uuid4
from typing import Any
from falkordb import FalkorDB
from .config import Settings
from .indicators import Indicator


class GraphError(Exception):
    pass


class GraphStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        try:
            self.db = FalkorDB(host=settings.falkordb_host, port=settings.falkordb_port,
                               socket_connect_timeout=2, socket_timeout=5)
            self.graph = self.db.select_graph(settings.falkordb_graph)
        except Exception as exc:
            raise GraphError(f"FalkorDB connection failed: {type(exc).__name__}") from exc

    def _query(self, cypher: str, params: dict[str, Any] | None = None) -> list[list[Any]]:
        try:
            result = self.graph.query(cypher, params=params or {})
            return result.result_set or []
        except Exception as exc:
            raise GraphError(f"FalkorDB query failed: {type(exc).__name__}: {exc}") from exc

    def initialize(self) -> None:
        for statement in (
            "CREATE INDEX FOR (i:Indicator) ON (i.key)",
            "CREATE INDEX FOR (e:Evidence) ON (e.id)",
            "CREATE INDEX FOR (o:Observation) ON (o.id)",
            "CREATE INDEX FOR (run:Investigation) ON (run.id)",
        ):
            try:
                self._query(statement)
            except GraphError as exc:
                # Existing index is expected on subsequent starts.
                if "already" not in str(exc).lower() and "exists" not in str(exc).lower():
                    raise

    def upsert_indicator(self, indicator: Indicator) -> None:
        self._query("MERGE (i:Indicator {key: $key}) SET i.kind=$kind, i.value=$value",
                    {"key": indicator.key, "kind": indicator.kind, "value": indicator.value})

    def add_observation(self, subject: Indicator, predicate: str, object_value: str,
                        source_id: str, source_url: str, fetched_at: str,
                        source_time: str = "", neighbor: Indicator | None = None) -> str:
        stable = f"{subject.key}|{predicate}|{object_value}|{source_id}"
        observation_id = hashlib.sha256(stable.encode()).hexdigest()[:24]
        evidence_id = hashlib.sha256(f"{source_id}|{subject.key}|{predicate}|{object_value}".encode()).hexdigest()[:24]
        params = {"subject": subject.key, "kind": subject.kind, "value": subject.value,
                  "oid": observation_id, "eid": evidence_id, "predicate": predicate,
                  "object": object_value[:500], "source_id": source_id, "url": source_url,
                  "fetched_at": fetched_at, "source_time": source_time[:100],
                  "neighbor": neighbor.key if neighbor else "", "neighbor_kind": neighbor.kind if neighbor else "",
                  "neighbor_value": neighbor.value if neighbor else ""}
        self._query("""
            MERGE (s:Indicator {key:$subject}) SET s.kind=$kind, s.value=$value
            MERGE (o:Observation {id:$oid}) SET o.predicate=$predicate, o.object=$object,
                o.source_time=$source_time, o.last_fetched_at=$fetched_at
            MERGE (e:Evidence {id:$eid}) SET e.source_id=$source_id, e.url=$url,
                e.last_fetched_at=$fetched_at
            MERGE (s)-[:HAS_OBSERVATION]->(o)
            MERGE (o)-[:SUPPORTED_BY]->(e)
        """, params)
        if neighbor:
            self._query("""
                MATCH (s:Indicator {key:$subject}), (o:Observation {id:$oid})
                MERGE (n:Indicator {key:$neighbor}) SET n.kind=$neighbor_kind, n.value=$neighbor_value
                MERGE (o)-[:POINTS_TO]->(n)
                MERGE (s)-[r:OBSERVED_LINK {observation_id:$oid}]->(n)
                SET r.predicate=$predicate
            """, params)
        return observation_id

    def get_evidence(self, indicator: Indicator, limit: int = 30) -> list[dict[str, Any]]:
        rows = self._query("""
            MATCH (i:Indicator {key:$key})-[:HAS_OBSERVATION]->(o:Observation)-[:SUPPORTED_BY]->(e:Evidence)
            OPTIONAL MATCH (o)-[:POINTS_TO]->(n:Indicator)
            RETURN o.id, o.predicate, o.object, o.source_time, o.last_fetched_at,
                   e.id, e.source_id, e.url, n.key
            ORDER BY o.last_fetched_at DESC LIMIT $limit
        """, {"key": indicator.key, "limit": min(max(limit, 1), 50)})
        return [{"id": r[0], "predicate": r[1], "object": r[2], "source_time": r[3],
                 "fetched_at": r[4], "evidence_id": r[5], "source_id": r[6], "source_url": r[7],
                 "neighbor_key": r[8]} for r in rows]

    def trace_paths(self, indicator: Indicator, depth: int = 2, limit: int = 30) -> dict[str, Any]:
        depth = min(max(depth, 1), 2)
        limit = min(max(limit, 1), 50)
        first = self._query("""
            MATCH (root:Indicator {key:$key})-[r:OBSERVED_LINK]-(n:Indicator)
            RETURN root.key, n.key, r.observation_id, r.predicate LIMIT $limit
        """, {"key": indicator.key, "limit": limit})
        paths = [{"nodes": [r[0], r[1]], "observation_ids": [r[2]],
                  "predicates": [r[3]], "type": "observed_path"}
                 for r in first]
        if depth == 2 and len(paths) < limit:
            second = self._query("""
                MATCH (root:Indicator {key:$key})-[r1:OBSERVED_LINK]-(mid:Indicator)
                      -[r2:OBSERVED_LINK]-(n:Indicator)
                WHERE n.key <> root.key
                RETURN root.key, mid.key, n.key, r1.observation_id, r2.observation_id,
                       r1.predicate, r2.predicate
                LIMIT $limit
            """, {"key": indicator.key, "limit": limit - len(paths)})
            paths.extend({"nodes": [r[0], r[1], r[2]], "observation_ids": [r[3], r[4]],
                          "predicates": [r[5], r[6]],
                          "type": "observed_path"} for r in second)
        keys = {indicator.key}
        for path in paths:
            keys.update(path["nodes"])
        nodes = [{"id": key, "kind": key.split(":", 1)[0], "label": key.split(":", 1)[1]} for key in sorted(keys)]
        edges = []
        edge_ids = set()
        for path in paths:
            for left, right, oid, predicate in zip(path["nodes"], path["nodes"][1:],
                                                    path["observation_ids"], path["predicates"]):
                if oid in edge_ids:
                    continue
                edge_ids.add(oid)
                edges.append({"id": oid, "source": left, "target": right, "kind": "observed",
                              "predicate": predicate, "observation_id": oid})
        return {"nodes": nodes, "edges": edges, "paths": paths, "depth": depth, "limit": limit,
                "truncated": len(paths) >= limit}

    def recent_neighbors(self, indicator: Indicator, limit: int = 5) -> list[str]:
        rows = self._query("""
            MATCH (i:Indicator {key:$key})-[:OBSERVED_LINK]-(n:Indicator)
            RETURN DISTINCT n.key LIMIT $limit
        """, {"key": indicator.key, "limit": min(max(limit, 1), 10)})
        return [r[0] for r in rows]

    def save_investigation(self, indicator: Indicator, result: dict[str, Any]) -> str:
        run_id = str(uuid4())
        snapshot = json.dumps(result, ensure_ascii=False, default=str)
        if len(snapshot) > 100_000:
            raise GraphError("Investigation snapshot exceeds the storage limit")
        self._query("""
            MATCH (i:Indicator {key:$key})
            CREATE (run:Investigation {id:$id, indicator:$key, created_at:$created_at,
                   status:$status, method:$method, snapshot:$snapshot})
            CREATE (i)-[:HAS_INVESTIGATION]->(run)
        """, {"key": indicator.key, "id": run_id, "created_at": result["report"]["generated_at"],
              "status": result["report"]["status"], "method": result["method"], "snapshot": snapshot})
        return run_id

    def list_investigations(self, limit: int = 10) -> list[dict[str, str]]:
        rows = self._query("""
            MATCH (run:Investigation)
            RETURN run.id, run.indicator, run.created_at, run.status, run.method
            ORDER BY run.created_at DESC LIMIT $limit
        """, {"limit": min(max(limit, 1), 20)})
        return [{"id": r[0], "indicator": r[1], "created_at": r[2], "status": r[3], "method": r[4]} for r in rows]

    def get_investigation(self, run_id: str) -> dict[str, Any] | None:
        rows = self._query("MATCH (run:Investigation {id:$id}) RETURN run.snapshot LIMIT 1", {"id": run_id})
        return json.loads(rows[0][0]) if rows else None

    def get_observation(self, observation_id: str) -> dict[str, Any] | None:
        rows = self._query("""
            MATCH (o:Observation {id:$id})-[:SUPPORTED_BY]->(e:Evidence)
            OPTIONAL MATCH (o)-[:POINTS_TO]->(n:Indicator)
            RETURN o.id, o.predicate, o.object, o.source_time, o.last_fetched_at,
                   e.id, e.source_id, e.url, n.key LIMIT 1
        """, {"id": observation_id})
        if not rows:
            return None
        r = rows[0]
        return {"id": r[0], "predicate": r[1], "object": r[2], "source_time": r[3],
                "fetched_at": r[4], "evidence_id": r[5], "source_id": r[6], "source_url": r[7],
                "neighbor_key": r[8]}
