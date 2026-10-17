from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from .indicators import Indicator, parse_indicator


DNS_ENDPOINT = "https://dns.google/resolve"


class DnsError(Exception):
    pass


@dataclass
class DnsResult:
    addresses: list[Indicator]
    fetched_at: str
    source_url: str


class DnsClient:
    async def lookup_a(self, domain: Indicator) -> DnsResult:
        if domain.kind != "domain":
            raise ValueError("Forward DNS lookup requires a domain")
        params = {"name": domain.value, "type": "A", "edns_client_subnet": "0.0.0.0/0"}
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(DNS_ENDPOINT, params=params)
                response.raise_for_status()
                payload: Any = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise DnsError(f"Current DNS lookup failed: {type(exc).__name__}.") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("Status"), int):
            raise DnsError("Current DNS lookup returned an unexpected response.")
        if payload["Status"] != 0:
            raise DnsError(f"Current DNS lookup returned DNS status {payload['Status']}.")
        addresses: list[Indicator] = []
        seen: set[str] = set()
        answers = payload.get("Answer")
        for answer in (answers if isinstance(answers, list) else [])[:30]:
            if not isinstance(answer, dict) or answer.get("type") != 1:
                continue
            try:
                address = parse_indicator(str(answer.get("data", "")))
            except Exception:
                continue
            if address.kind != "IPv4" or address.key in seen:
                continue
            seen.add(address.key)
            addresses.append(address)
            if len(addresses) >= 5:
                break
        return DnsResult(addresses, datetime.now(timezone.utc).isoformat(), str(response.url))
