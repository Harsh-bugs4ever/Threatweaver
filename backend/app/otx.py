from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote
import httpx
from .indicators import Indicator, parse_indicator


@dataclass
class OtxResult:
    general: dict[str, Any]
    passive_dns: dict[str, Any]
    fetched_at: str
    warnings: list[str] = field(default_factory=list)


class OtxError(Exception):
    pass


class OtxClient:
    def __init__(self, api_key: str | None, base_url: str, timeout: float = 12.0):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def lookup(self, indicator: Indicator) -> OtxResult:
        if not self.api_key:
            raise OtxError("OTX_API_KEY is not configured. Add it to .env to fetch live intelligence.")
        kind = "domain" if indicator.kind == "domain" else "IPv4"
        stem = f"/api/v1/indicators/{kind}/{quote(indicator.value, safe='')}"
        headers = {"X-OTX-API-KEY": self.api_key, "Accept": "application/json"}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout, headers=headers) as client:
            try:
                general_response = await client.get(stem + "/general")
                self._check(general_response)
                general = general_response.json()
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                raise OtxError(f"OTX general lookup is unreachable: {type(exc).__name__}.") from exc
            except (ValueError, TypeError) as exc:
                raise OtxError("OTX general lookup returned invalid JSON.") from exc
            if not isinstance(general, dict):
                raise OtxError("OTX general lookup returned an unexpected response shape.")

            warnings: list[str] = []
            try:
                passive_response = await client.get(stem + "/passive_dns")
                self._check(passive_response)
                passive = passive_response.json()
                if not isinstance(passive, dict):
                    raise OtxError("OTX passive DNS returned an unexpected response shape.")
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                passive = {}
                warnings.append(f"OTX passive DNS is unreachable: {type(exc).__name__}. General intelligence is available.")
            except (ValueError, TypeError):
                passive = {}
                warnings.append("OTX passive DNS returned invalid JSON. General intelligence is available.")
            except OtxError as exc:
                passive = {}
                warnings.append(f"{exc} General intelligence is available.")
        return OtxResult(general, passive, datetime.now(timezone.utc).isoformat(), warnings)

    @staticmethod
    def _check(response: httpx.Response) -> None:
        if response.status_code in (401, 403):
            raise OtxError("OTX rejected the API key or access is forbidden.")
        if response.status_code == 404:
            raise OtxError("OTX has no record for this indicator.")
        if response.status_code == 429:
            raise OtxError("OTX rate limit reached. Try again later.")
        if response.status_code >= 400:
            raise OtxError(f"OTX request failed with HTTP {response.status_code}.")


def extract_dns(indicator: Indicator, payload: dict[str, Any], limit: int = 12) -> list[dict[str, str]]:
    records = payload.get("passive_dns", [])
    if not isinstance(records, list):
        return []
    found: list[dict[str, str]] = []
    seen: set[str] = set()
    for record in records[:100]:
        if not isinstance(record, dict):
            continue
        raw = record.get("address") if indicator.kind == "domain" else record.get("hostname")
        if not isinstance(raw, str):
            continue
        try:
            neighbor = parse_indicator(raw)
        except Exception:
            continue
        if neighbor.kind == indicator.kind or neighbor.key == indicator.key or neighbor.key in seen:
            continue
        seen.add(neighbor.key)
        found.append({"key": neighbor.key, "kind": neighbor.kind, "value": neighbor.value,
                      "first_seen": str(record.get("first") or ""), "last_seen": str(record.get("last") or "")})
        if len(found) >= limit:
            break
    return found
