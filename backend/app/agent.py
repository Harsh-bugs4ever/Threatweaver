import json
from datetime import datetime, timezone
from typing import Any
import httpx
from .config import Settings
from .graph import GraphStore
from .indicators import Indicator, parse_indicator
from .investigation import persist_otx
from .otx import OtxClient, OtxError


TOOLS = [
    {"type": "function", "function": {"name": "trace_paths", "description": "Read observed graph paths, at most two hops.",
      "parameters": {"type": "object", "properties": {"depth": {"type": "integer", "minimum": 1, "maximum": 2}}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "get_evidence", "description": "Read stored source evidence for the root indicator.",
      "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "lookup_indicator", "description": "Fetch OTX for one observed graph neighbor only.",
      "parameters": {"type": "object", "properties": {"indicator": {"type": "string"}}, "required": ["indicator"], "additionalProperties": False}}},
]


async def run_agent(root: Indicator, graph: GraphStore, otx: OtxClient, settings: Settings,
                    current_keys: list[str]) -> dict[str, Any]:
    if not settings.deepseek_api_key:
        return {"status": "not_configured", "message": "DEEPSEEK_API_KEY is absent; deterministic graph-guided investigation was used.", "audit": []}
    allowed = set(graph.recent_neighbors(root, 10)).intersection(current_keys)
    audit: list[dict[str, Any]] = []
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": "You are a security triage tool planner. Use tools to inspect evidence and observed graph links. Never claim compromise, malicious intent, or a verified threat from association alone. The deterministic report remains authoritative. Keep any final note brief and state uncertainty."},
        {"role": "user", "content": f"Investigate {root.key}. Allowed OTX pivot indicators: {sorted(allowed)}. Select bounded tools to inspect. Do not invent findings."},
    ]
    lookups = 0
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            for iteration in range(3):
                response = await client.post("https://api.deepseek.com/chat/completions",
                    headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
                    json={"model": settings.deepseek_model, "messages": messages, "tools": TOOLS,
                          "tool_choice": "auto", "thinking": {"type": "disabled"},
                          "temperature": 0, "max_tokens": 350})
                response.raise_for_status()
                payload = response.json()
                choice = payload["choices"][0]["message"]
                calls = choice.get("tool_calls") or []
                if not calls:
                    return {"status": "complete", "message": str(choice.get("content") or "")[:1000], "audit": audit}
                if len(calls) > 3:
                    return {"status": "tool_limit", "message": "Agent requested more than three tools in one iteration.", "audit": audit}
                messages.append(choice)
                for call in calls[:3]:
                    name = call.get("function", {}).get("name", "")
                    args: dict[str, Any] = {}
                    try:
                        args = json.loads(call.get("function", {}).get("arguments") or "{}")
                        if not isinstance(args, dict):
                            raise ValueError("Arguments must be an object")
                        if name == "trace_paths":
                            depth = args.get("depth", 2)
                            if type(depth) is not int or depth not in (1, 2):
                                raise ValueError("Depth must be 1 or 2")
                            data = graph.trace_paths(root, depth, 20)
                        elif name == "get_evidence":
                            data = graph.get_evidence(root, 20)
                        elif name == "lookup_indicator":
                            indicator = parse_indicator(str(args.get("indicator", "")))
                            if indicator.key not in allowed or lookups >= 1:
                                raise ValueError("Only one observed neighbor lookup is allowed")
                            lookups += 1
                            data = persist_otx(graph, otx, indicator, await otx.lookup(indicator))
                        else:
                            raise ValueError("Unknown tool")
                        status = "ok"
                    except Exception as exc:
                        data = {"error": str(exc)[:250]}
                        status = "error"
                    audit.append({"iteration": iteration + 1, "tool": name[:50], "arguments": args,
                                  "status": status, "at": datetime.now(timezone.utc).isoformat()})
                    messages.append({"role": "tool", "tool_call_id": call["id"],
                                     "content": json.dumps(data, default=str)[:6000]})
            return {"status": "iteration_limit", "message": "Agent stopped at the three-iteration limit.", "audit": audit}
    except (httpx.HTTPError, KeyError, ValueError, TypeError) as exc:
        return {"status": "failed", "message": f"DeepSeek tool planning failed: {type(exc).__name__}.", "audit": audit}
