from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote
from .dns import DnsClient, DnsError, DnsResult
from .graph import GraphStore
from .indicators import Indicator, parse_indicator
from .otx import OtxClient, OtxError, OtxResult, extract_dns


MAX_PIVOTS = 1


def source_url(otx: OtxClient, indicator: Indicator, section: str) -> str:
    kind = "domain" if indicator.kind == "domain" else "IPv4"
    return f"{otx.base_url}/api/v1/indicators/{kind}/{quote(indicator.value, safe='')}/{section}"


def persist_otx(graph: GraphStore, otx: OtxClient, indicator: Indicator, result: OtxResult) -> dict[str, Any]:
    graph.upsert_indicator(indicator)
    general = result.general
    pulse_info = general.get("pulse_info") if isinstance(general.get("pulse_info"), dict) else {}
    count = pulse_info.get("count")
    if not isinstance(count, int) or count < 0:
        count = None
    if count is not None:
        graph.add_observation(indicator, "otx_pulse_count", str(count),
                              f"otx:{indicator.key}:general", source_url(otx, indicator, "general"), result.fetched_at)
    pulses = pulse_info.get("pulses") if isinstance(pulse_info.get("pulses"), list) else []
    pulse_names = []
    for pulse in pulses[:5]:
        if not isinstance(pulse, dict) or not isinstance(pulse.get("id"), str):
            continue
        name = str(pulse.get("name") or "Unnamed OTX pulse")[:160]
        pulse_names.append(name)
        graph.add_observation(indicator, "otx_pulse", name,
                              f"otx:pulse:{pulse['id']}", source_url(otx, indicator, "general"), result.fetched_at)
    dns = extract_dns(indicator, result.passive_dns)
    for neighbor_data in dns:
        neighbor = Indicator(neighbor_data["kind"], neighbor_data["value"])
        graph.add_observation(indicator, "passive_dns", neighbor.key,
                              f"otx:{indicator.key}:passive_dns:{neighbor.key}",
                              source_url(otx, indicator, "passive_dns"), result.fetched_at,
                              neighbor_data["last_seen"], neighbor)
    return {"pulse_count": count, "pulse_names": pulse_names,
            "dns_count": len(dns) if not result.warnings else None,
            "dns_keys": [item["key"] for item in dns], "fetched_at": result.fetched_at,
            "source_warnings": result.warnings}


def persist_live_dns(graph: GraphStore, domain: Indicator, result: DnsResult) -> list[str]:
    for address in result.addresses:
        graph.add_observation(domain, "current_dns_a", address.key,
                              f"google-dns:{domain.key}:A:{address.key}", result.source_url,
                              result.fetched_at, result.fetched_at, address)
    return [address.key for address in result.addresses]


def make_report(indicator: Indicator, findings: dict[str, Any], graph_data: dict[str, Any],
                evidence: list[dict[str, Any]], pivot: dict[str, Any] | None,
                warnings: list[str]) -> dict[str, Any]:
    pulse_count = findings.get("pulse_count")
    dns_count = findings.get("dns_count", 0)
    live_dns_count = findings.get("live_dns_count")
    observations = []
    if pulse_count is not None:
        observations.append(f"OTX lists {pulse_count} pulse(s) for {indicator.value}.")
    if dns_count:
        observations.append(f"OTX passive DNS returned {dns_count} related indicator(s) in this bounded sample.")
    if live_dns_count is not None:
        observations.append(f"Google Public DNS returned {live_dns_count} current IPv4 answer(s) for {indicator.value}.")
    if not observations:
        observations.append(f"Current OTX lookup produced no verified finding; {len(evidence)} previously stored observation(s) are shown." if evidence
                            else "No supported OTX finding was available for this investigation.")
    observation_refs = [{"observation_id": item["id"], "evidence_id": item["evidence_id"],
                         "source_id": item["source_id"]} for item in evidence[:10]]
    inferred = []
    if graph_data["paths"]:
        inferred.append("Observed DNS links offer investigation pivots; a shared link alone does not establish malicious activity.")
    actions = []
    if pulse_count and pulse_count > 0:
        actions.append("Review the linked OTX pulses and validate relevance before escalating this indicator.")
    if pivot:
        actions.append(f"Review {pivot['indicator']} as the first related indicator, selected from observed graph links.")
    if dns_count:
        actions.append("Compare passive DNS timestamps with internal telemetry before drawing a conclusion.")
    if live_dns_count:
        actions.append("Check whether the currently resolved IP addresses appear in your own DNS or network logs.")
    if not actions:
        actions.append("Collect additional trusted telemetry before deciding whether to escalate.")
    confidence = "limited" if pulse_count is None else "source_observations_only"
    return {"indicator": indicator.key, "status": "complete" if not warnings else "partial",
            "data_freshness": "current_external_fetch" if findings.get("fetched_at") or findings.get("live_dns_fetched_at") else "stored_graph_only",
            "observations": observations, "observation_refs": observation_refs, "inferences": inferred,
            "unknowns": ["OTX context alone cannot establish compromise or intent.",
                         "Internal asset exposure and traffic are unknown."],
            "recommended_actions": actions, "confidence": confidence,
            "evidence_count": len(evidence), "warnings": warnings,
            "generated_at": datetime.now(timezone.utc).isoformat()}


async def investigate(indicator: Indicator, graph: GraphStore, otx: OtxClient, expand: bool = True,
                      dns: DnsClient | None = None) -> dict[str, Any]:
    graph.upsert_indicator(indicator)
    warnings: list[str] = []
    findings: dict[str, Any] = {}
    try:
        findings = persist_otx(graph, otx, indicator, await otx.lookup(indicator))
        warnings.extend(findings["source_warnings"])
    except OtxError as exc:
        warnings.append(str(exc))
    if dns is not None and indicator.kind == "domain":
        try:
            live_dns = await dns.lookup_a(indicator)
            findings["live_dns_keys"] = persist_live_dns(graph, indicator, live_dns)
            findings["live_dns_count"] = len(live_dns.addresses)
            findings["live_dns_fetched_at"] = live_dns.fetched_at
        except DnsError as exc:
            warnings.append(str(exc))
    pivot = None
    # The graph decides the first follow-up. Only observed links qualify and at most one is queried.
    current_keys = set(findings.get("dns_keys", []) + findings.get("live_dns_keys", []))
    if expand and current_keys:
        neighbors = [key for key in graph.recent_neighbors(indicator, 10) if key in current_keys][:MAX_PIVOTS]
        if neighbors:
            chosen = parse_indicator(neighbors[0].split(":", 1)[1])
            source_label = "current Google Public DNS answer" if chosen.key in findings.get("live_dns_keys", []) else "OTX passive DNS observation"
            pivot = {"indicator": chosen.key, "reason": f"Graph link from a {source_label}, persisted in FalkorDB",
                     "lookup_status": "not_attempted"}
            try:
                pivot["findings"] = persist_otx(graph, otx, chosen, await otx.lookup(chosen))
                if pivot["findings"]["source_warnings"]:
                    pivot["lookup_status"] = "partial"
                    warnings.extend(f"Pivot lookup: {warning}" for warning in pivot["findings"]["source_warnings"])
                else:
                    pivot["lookup_status"] = "complete"
            except OtxError as exc:
                pivot["lookup_status"] = "failed"
                pivot["error"] = str(exc)
                warnings.append(f"Pivot lookup failed: {exc}")
    graph_data = graph.trace_paths(indicator, depth=2, limit=30)
    evidence = graph.get_evidence(indicator, limit=30)
    report = make_report(indicator, findings, graph_data, evidence, pivot, warnings)
    return {"report": report, "findings": findings, "pivot": pivot,
            "graph": graph_data, "evidence": evidence,
            "method": "bounded_graph_guided_investigation"}
