from contextlib import asynccontextmanager
from functools import lru_cache
from uuid import UUID
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .config import get_settings
from .dns import DnsClient
from .graph import GraphError, GraphStore
from .indicators import parse_indicator
from .investigation import investigate, persist_otx
from .otx import OtxClient, OtxError
from .agent import run_agent


@lru_cache
def get_graph() -> GraphStore:
    return GraphStore(get_settings())


def get_otx() -> OtxClient:
    s = get_settings()
    return OtxClient(s.otx_api_key, s.otx_base_url, s.otx_timeout_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup stays available for informative health/error responses if the DB is down.
    try:
        get_graph().initialize()
        app.state.graph_ready = True
    except Exception:
        app.state.graph_ready = False
    yield


app = FastAPI(title="ThreatWeaver API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origins.split(","),
                   allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


class InvestigationRequest(BaseModel):
    indicator: str = Field(min_length=3, max_length=253)
    expand: bool = True
    use_agent: bool = False


@app.exception_handler(GraphError)
async def graph_error_handler(request, exc: GraphError):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=503, content={"detail": "FalkorDB is unavailable or rejected a query. Check the service and server logs.",
                                                  "code": "graph_unavailable"})


@app.get("/api/health")
def health():
    try:
        graph = get_graph()
        graph._query("RETURN 1")
        db = "ready"
    except Exception:
        db = "unavailable"
    return {"service": "ready", "graph": db, "otx_configured": bool(get_settings().otx_api_key),
            "llm_configured": bool(get_settings().deepseek_api_key)}


@app.post("/api/investigations")
async def run_investigation(body: InvestigationRequest):
    indicator = parse_indicator(body.indicator)
    graph = get_graph()
    otx = get_otx()
    result = await investigate(indicator, graph, otx, body.expand, DnsClient())
    current_keys = result["findings"].get("dns_keys", []) + result["findings"].get("live_dns_keys", [])
    result["agent"] = await run_agent(indicator, graph, otx, get_settings(), current_keys) if body.use_agent else {
        "status": "not_requested", "message": "Deterministic graph-guided investigation used.", "audit": []}
    result["investigation_id"] = graph.save_investigation(indicator, result)
    return result


@app.get("/api/investigations")
def list_investigations(limit: int = Query(10, ge=1, le=20)):
    return {"items": get_graph().list_investigations(limit)}


@app.get("/api/investigations/{investigation_id}")
def get_investigation(investigation_id: UUID):
    result = get_graph().get_investigation(str(investigation_id))
    if result is None:
        raise HTTPException(404, "Investigation not found.")
    result["investigation_id"] = str(investigation_id)
    return result


@app.get("/api/observations/{observation_id}")
def get_observation(observation_id: str):
    if len(observation_id) != 24 or any(c not in "0123456789abcdef" for c in observation_id):
        raise HTTPException(422, "Invalid observation ID.")
    result = get_graph().get_observation(observation_id)
    if result is None:
        raise HTTPException(404, "Observation not found.")
    return result


@app.get("/api/tools/lookup_indicator")
async def lookup_indicator(indicator: str = Query(max_length=253)):
    parsed = parse_indicator(indicator)
    graph = get_graph()
    otx = get_otx()
    try:
        result = await otx.lookup(parsed)
    except OtxError as exc:
        raise HTTPException(502, str(exc)) from exc
    return {"indicator": parsed.key, "findings": persist_otx(graph, otx, parsed, result)}


@app.get("/api/tools/trace_paths")
def trace_paths(indicator: str = Query(max_length=253), depth: int = Query(2, ge=1, le=2),
                limit: int = Query(30, ge=1, le=50)):
    parsed = parse_indicator(indicator)
    return get_graph().trace_paths(parsed, depth, limit)


@app.get("/api/tools/get_evidence")
def get_evidence(indicator: str = Query(max_length=253), limit: int = Query(30, ge=1, le=50)):
    parsed = parse_indicator(indicator)
    return {"indicator": parsed.key, "evidence": get_graph().get_evidence(parsed, limit)}
