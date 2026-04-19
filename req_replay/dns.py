"""DNS resolution analysis for captured requests."""
from __future__ import annotations

import socket
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

from req_replay.models import CapturedRequest


@dataclass
class DNSResult:
    host: str
    resolved: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def reachable(self) -> bool:
        return bool(self.resolved)

    def display(self) -> str:
        lines = [f"Host : {self.host}"]
        if self.error:
            lines.append(f"Error: {self.error}")
        else:
            lines.append(f"IPs  : {', '.join(self.resolved)}")
            lines.append(f"Status: {'reachable' if self.reachable else 'unresolved'}")
        return "\n".join(lines)


def resolve_host(host: str, timeout: float = 5.0) -> DNSResult:
    """Resolve a hostname to IP addresses."""
    try:
        old = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)
        try:
            infos = socket.getaddrinfo(host, None)
        finally:
            socket.setdefaulttimeout(old)
        ips = list(dict.fromkeys(i[4][0] for i in infos))
        return DNSResult(host=host, resolved=ips)
    except socket.gaierror as exc:
        return DNSResult(host=host, error=str(exc))


def analyze_dns(requests: List[CapturedRequest], timeout: float = 5.0) -> List[DNSResult]:
    """Resolve unique hosts from a list of captured requests."""
    seen: dict[str, DNSResult] = {}
    for req in requests:
        host = urlparse(req.url).hostname or ""
        if host and host not in seen:
            seen[host] = resolve_host(host, timeout=timeout)
    return list(seen.values())
