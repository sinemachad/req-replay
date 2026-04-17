"""TLS/SSL certificate inspection for captured requests."""
from __future__ import annotations

import ssl
import socket
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional


@dataclass
class TLSInfo:
    host: str
    port: int
    subject: dict
    issuer: dict
    version: str
    expires: Optional[datetime]
    san: list[str] = field(default_factory=list)

    def expired(self) -> bool:
        if self.expires is None:
            return False
        return datetime.utcnow() > self.expires

    def days_until_expiry(self) -> Optional[int]:
        if self.expires is None:
            return None
        delta = self.expires - datetime.utcnow()
        return delta.days

    def display(self) -> str:
        lines = [
            f"Host:    {self.host}:{self.port}",
            f"Subject: {self.subject}",
            f"Issuer:  {self.issuer}",
            f"Version: {self.version}",
            f"Expires: {self.expires.isoformat() if self.expires else 'unknown'}",
            f"SAN:     {', '.join(self.san) if self.san else 'none'}",
            f"Expired: {self.expired()}",
        ]
        return "\n".join(lines)


def _parse_rdn(rdn_seq) -> dict:
    result = {}
    for rdn in rdn_seq:
        for key, value in rdn:
            result[key] = value
    return result


def inspect_tls(url: str, timeout: float = 5.0) -> TLSInfo:
    parsed = urlparse(url)
    host = parsed.hostname or url
    port = parsed.port or 443

    ctx = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=timeout) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as ssock:
            cert = ssock.getpeercert()

    subject = _parse_rdn(cert.get("subject", []))
    issuer = _parse_rdn(cert.get("issuer", []))
    version = cert.get("version", "unknown")

    not_after = cert.get("notAfter")
    expires = None
    if not_after:
        expires = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")

    san = [
        value
        for kind, value in cert.get("subjectAltName", [])
        if kind == "DNS"
    ]

    return TLSInfo(
        host=host,
        port=port,
        subject=subject,
        issuer=issuer,
        version=str(version),
        expires=expires,
        san=san,
    )
