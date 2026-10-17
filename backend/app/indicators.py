import ipaddress
import re
from dataclasses import dataclass
from fastapi import HTTPException


DOMAIN_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


@dataclass(frozen=True)
class Indicator:
    kind: str
    value: str

    @property
    def key(self) -> str:
        return f"{self.kind}:{self.value}"


def parse_indicator(raw: str) -> Indicator:
    value = raw.strip().lower().rstrip(".")
    if not value or len(value) > 253 or "/" in value or ":" in value:
        raise HTTPException(422, "Enter one domain or public IPv4 address.")
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        address = None
    if address is not None:
        if not isinstance(address, ipaddress.IPv4Address) or not address.is_global:
            raise HTTPException(422, "Enter a public IPv4 address.")
        return Indicator("IPv4", str(address))
    labels = value.split(".")
    if len(labels) < 2 or any(not DOMAIN_LABEL.fullmatch(label) for label in labels) or labels[-1].isdigit():
        raise HTTPException(422, "Enter a valid domain or public IPv4 address.")
    try:
        ascii_domain = value.encode("idna").decode("ascii")
    except UnicodeError:
        raise HTTPException(422, "Enter a valid domain.") from None
    if len(ascii_domain) > 253:
        raise HTTPException(422, "Domain is too long.")
    return Indicator("domain", ascii_domain)
