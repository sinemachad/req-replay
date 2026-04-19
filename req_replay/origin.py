"""Analyze request origins (IP, referer, user-agent) across captured requests."""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import Counter
from typing import List, Optional

from req_replay.models import CapturedRequest


@dataclass
class OriginStats:
    total: int = 0
    top_ips: List[tuple] = field(default_factory=list)
    top_referers: List[tuple] = field(default_factory=list)
    top_user_agents: List[tuple] = field(default_factory=list)

    def display(self) -> str:
        lines = [f"Total requests: {self.total}"]
        if self.top_ips:
            lines.append("Top IPs:")
            for ip, count in self.top_ips:
                lines.append(f"  {ip}: {count}")
        if self.top_referers:
            lines.append("Top Referers:")
            for ref, count in self.top_referers:
                lines.append(f"  {ref}: {count}")
        if self.top_user_agents:
            lines.append("Top User-Agents:")
            for ua, count in self.top_user_agents:
                lines.append(f"  {ua}: {count}")
        return "\n".join(lines)


def _header_value(req: CapturedRequest, name: str) -> Optional[str]:
    for k, v in (req.headers or {}).items():
        if k.lower() == name.lower():
            return v
    return None


def analyze_origins(requests: List[CapturedRequest], top_n: int = 5) -> OriginStats:
    if not requests:
        return OriginStats()

    ip_counter: Counter = Counter()
    ref_counter: Counter = Counter()
    ua_counter: Counter = Counter()

    for req in requests:
        ip = _header_value(req, "x-forwarded-for") or _header_value(req, "x-real-ip")
        if ip:
            ip_counter[ip.split(",")[0].strip()] += 1

        ref = _header_value(req, "referer") or _header_value(req, "referrer")
        if ref:
            ref_counter[ref] += 1

        ua = _header_value(req, "user-agent")
        if ua:
            ua_counter[ua] += 1

    return OriginStats(
        total=len(requests),
        top_ips=ip_counter.most_common(top_n),
        top_referers=ref_counter.most_common(top_n),
        top_user_agents=ua_counter.most_common(top_n),
    )
