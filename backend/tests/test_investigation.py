import asyncio
import json
from datetime import datetime, timezone
import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from backend.app import main as api
from backend.app.agent import run_agent
from backend.app.config import Settings
from backend.app.dns import DnsClient, DnsResult
from backend.app.graph import GraphError, GraphStore
from backend.app.indicators import Indicator, parse_indicator
from backend.app.investigation import investigate, make_report
from backend.app.otx import OtxClient, OtxError, OtxResult, extract_dns


@pytest.mark.parametrize("value", ["127.0.0.1", "10.0.0.1", "2001:4860:4860::8888", "bad_domain", "example.com/path", "8.8.8.8; MATCH (n)"])
def test_rejects_invalid_or_private_indicators(value):
    with pytest.raises(HTTPException):
        parse_indicator(value)


def test_normalizes_domain_and_public_ip():
    assert parse_indicator(" Example.COM. ").key == "domain:example.com"
    assert parse_indicator("8.8.8.8").key == "IPv4:8.8.8.8"


def test_otx_status_errors_are_explicit():
    for status, fragment in [(401, "API key"), (404, "no record"), (429, "rate limit"), (500, "HTTP 500")]:
        with pytest.raises(OtxError, match=fragment):
            OtxClient._check(httpx.Response(status))


def test_missing_key_is_an_explicit_source_error():
    with pytest.raises(OtxError, match="OTX_API_KEY"):
        asyncio.run(OtxClient(None, "https://otx.alienvault.com").lookup(parse_indicator("example.com")))


def test_otx_keeps_general_result_when_passive_dns_times_out(monkeypatch):
    def respond(request):
        if request.url.path.endswith("/general"):
            return httpx.Response(200, json={"pulse_info": {"count": 2}})
        raise httpx.ReadTimeout("Passive DNS did not respond", request=request)

    original_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original_client(transport=httpx.MockTransport(respond), **kwargs))
    result = asyncio.run(OtxClient("test-key", "https://otx.alienvault.com").lookup(parse_indicator("example.com")))

    assert result.general["pulse_info"]["count"] == 2
    assert result.passive_dns == {}
    assert "passive DNS" in result.warnings[0]


def test_current_dns_answers_are_validated_and_bounded(monkeypatch):
    def respond(request):
        assert request.url.params["name"] == "example.com"
        assert request.url.params["type"] == "A"
        return httpx.Response(200, json={"Status": 0, "Answer": [
            {"type": 1, "data": "8.8.8.8"}, {"type": 1, "data": "8.8.8.8"},
            {"type": 1, "data": "127.0.0.1"}, {"type": 5, "data": "alias.example.com."}]})

    original_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original_client(transport=httpx.MockTransport(respond), **kwargs))
    result = asyncio.run(DnsClient().lookup_a(parse_indicator("example.com")))
    assert [address.key for address in result.addresses] == ["IPv4:8.8.8.8"]
    assert result.source_url.startswith("https://dns.google/resolve?")


def test_api_validates_before_graph_and_returns_service_error(monkeypatch):
    def unavailable():
        raise GraphError("connection refused")
    monkeypatch.setattr(api, "get_graph", unavailable)
    client = TestClient(api.app)
    assert client.post("/api/investigations", json={"indicator": "127.0.0.1"}).status_code == 422
    response = client.post("/api/investigations", json={"indicator": "example.com"})
    assert response.status_code == 503
    assert response.json()["code"] == "graph_unavailable"


def test_dns_extraction_is_validated_deduplicated_and_bounded():
    root = parse_indicator("example.com")
    records = [{"address": "8.8.8.8"}, {"address": "8.8.8.8"}, {"address": "127.0.0.1"},
               {"address": "1.1.1.1"}]
    found = extract_dns(root, {"passive_dns": records}, limit=1)
    assert [item["key"] for item in found] == ["IPv4:8.8.8.8"]


def test_graph_paths_are_bounded_and_parameterized():
    graph = object.__new__(GraphStore)
    seen = []
    graph._query = lambda cypher, params: (seen.append((cypher, params)) or [])
    output = graph.trace_paths(parse_indicator("example.com"), depth=999, limit=999)
    assert output["depth"] == 2 and output["limit"] == 50
    assert "[r:OBSERVED_LINK]" in seen[0][0]
    assert "[r1:OBSERVED_LINK]" in seen[1][0]
    assert seen[0][1] == {"key": "domain:example.com", "limit": 50}
    assert "example.com" not in seen[0][0]


def test_investigation_snapshot_persists_agent_audit():
    graph = object.__new__(GraphStore)
    seen = []
    graph._query = lambda cypher, params: (seen.append((cypher, params)) or [])
    result = {"report": {"generated_at": "2026-10-17T00:00:00Z", "status": "complete"},
              "method": "bounded_graph_guided_investigation",
              "agent": {"status": "complete", "audit": [{"tool": "get_evidence", "status": "ok"}]}}
    run_id = graph.save_investigation(parse_indicator("example.com"), result)
    assert len(run_id) == 36
    assert seen[0][1]["key"] == "domain:example.com"
    assert '"get_evidence"' in seen[0][1]["snapshot"]


class FakeGraph:
    def __init__(self):
        self.observations = []
        self.lookup_keys = []

    def upsert_indicator(self, indicator):
        pass

    def add_observation(self, subject, predicate, object_value, source_id, source_url, fetched_at,
                        source_time="", neighbor=None):
        self.observations.append((subject.key, predicate, object_value, source_id, neighbor.key if neighbor else None))
        return "observation-id"

    def recent_neighbors(self, indicator, limit):
        return self.lookup_keys[:limit]

    def trace_paths(self, indicator, depth, limit):
        return {"nodes": [], "edges": [], "paths": [], "depth": depth, "limit": limit, "truncated": False}

    def get_evidence(self, indicator, limit):
        return []


class FakeOtx:
    base_url = "https://otx.alienvault.com"

    def __init__(self, dns=None, failure=False):
        self.dns = dns or []
        self.failure = failure
        self.calls = []

    async def lookup(self, indicator):
        self.calls.append(indicator.key)
        if self.failure:
            raise OtxError("OTX rate limit reached. Try again later.")
        return OtxResult({"pulse_info": {"count": 0}}, {"passive_dns": self.dns},
                         datetime.now(timezone.utc).isoformat())


class FakeDns:
    async def lookup_a(self, indicator):
        return DnsResult([parse_indicator("8.8.8.8")], datetime.now(timezone.utc).isoformat(),
                         "https://dns.google/resolve?name=example.com&type=A")


def test_missing_source_is_partial_without_invented_findings():
    result = asyncio.run(investigate(parse_indicator("example.com"), FakeGraph(), FakeOtx(failure=True)))
    assert result["report"]["status"] == "partial"
    assert result["findings"] == {}
    assert result["pivot"] is None
    assert all("compromised" not in item.lower() for item in result["report"]["observations"])


def test_stale_graph_neighbor_is_not_used_as_current_pivot():
    graph = FakeGraph()
    graph.lookup_keys = ["IPv4:8.8.8.8"]
    otx = FakeOtx(dns=[])
    result = asyncio.run(investigate(parse_indicator("example.com"), graph, otx))
    assert result["pivot"] is None
    assert otx.calls == ["domain:example.com"]


def test_current_observed_graph_neighbor_is_followed_once():
    graph = FakeGraph()
    graph.lookup_keys = ["IPv4:8.8.8.8", "IPv4:1.1.1.1"]
    otx = FakeOtx(dns=[{"address": "8.8.8.8"}, {"address": "1.1.1.1"}])
    result = asyncio.run(investigate(parse_indicator("example.com"), graph, otx))
    assert result["pivot"]["indicator"] == "IPv4:8.8.8.8"
    assert otx.calls == ["domain:example.com", "IPv4:8.8.8.8"]


def test_current_dns_link_is_sourced_and_can_drive_graph_pivot():
    graph = FakeGraph()
    graph.lookup_keys = ["IPv4:8.8.8.8"]
    otx = FakeOtx(dns=[])
    result = asyncio.run(investigate(parse_indicator("example.com"), graph, otx, dns=FakeDns()))
    assert result["findings"]["live_dns_count"] == 1
    assert any(item[1] == "current_dns_a" and item[4] == "IPv4:8.8.8.8" for item in graph.observations)
    assert result["pivot"]["indicator"] == "IPv4:8.8.8.8"
    assert "current Google Public DNS" in result["pivot"]["reason"]


def test_report_describes_association_as_inference_with_unknowns():
    report = make_report(parse_indicator("example.com"), {"pulse_count": 0, "dns_count": 1},
                         {"paths": [{"nodes": ["domain:example.com", "IPv4:8.8.8.8"]}]}, [], None, [])
    assert "0 pulse" in report["observations"][0]
    assert "does not establish malicious activity" in report["inferences"][0]
    assert any("cannot establish compromise" in item for item in report["unknowns"])


def test_agent_uses_current_deepseek_flash_tool_api(monkeypatch):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": "Insufficient evidence.", "tool_calls": []}}]})

    original_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original_client(transport=httpx.MockTransport(respond), **kwargs))
    settings = Settings(_env_file=None, deepseek_api_key="test-key", deepseek_model="deepseek-flash")
    result = asyncio.run(run_agent(parse_indicator("example.com"), FakeGraph(), FakeOtx(), settings, []))

    assert result["status"] == "complete"
    assert len(requests) == 1
    request = requests[0]
    assert str(request.url) == "https://api.deepseek.com/chat/completions"
    assert request.headers["authorization"] == "Bearer test-key"
    body = json.loads(request.content)
    assert body["model"] == "deepseek-flash"
    assert body["thinking"] == {"type": "disabled"}
    assert {tool["function"]["name"] for tool in body["tools"]} == {"trace_paths", "get_evidence", "lookup_indicator"}
