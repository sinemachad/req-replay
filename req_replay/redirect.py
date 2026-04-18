"""Track and analyze HTTP redirect chains in captured request/response pairs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from req_replay.models import CapturedRequest, CapturedResponse


@dataclass
class RedirectHop:
    url: str
    status_code: int
    location: Optional[str]

    def to_dict(self) -> dict:
        return {"url": self.url, "status_code": self.status_code, "location": self.location}


@dataclass
class RedirectChain:
    hops: List[RedirectHop] = field(default_factory=list)

    @property
    def length(self) -> int:
        return len(self.hops)

    @property
    def is_redirect_loop(self) -> bool:
        seen = [h.url for h in self.hops]
        return len(seen) != len(set(seen))

    @property
    def final_url(self) -> Optional[str]:
        if not self.hops:
            return None
        last = self.hops[-1]
        return last.location if last.location else last.url

    def display(self) -> str:
        if not self.hops:
            return "No redirects."
        lines = [f"Redirect chain ({self.length} hop(s)):"]
        for i, hop in enumerate(self.hops, 1):
            lines.append(f"  {i}. [{hop.status_code}] {hop.url} -> {hop.location or '(none)'}")
        if self.is_redirect_loop:
            lines.append("  WARNING: redirect loop detected")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "hops": [h.to_dict() for h in self.hops],
            "length": self.length,
            "is_redirect_loop": self.is_redirect_loop,
            "final_url": self.final_url,
        }


REDIRECT_CODES = {301, 302, 303, 307, 308}


def analyze_redirects(
    pairs: List[Tuple[CapturedRequest, CapturedResponse]],
) -> RedirectChain:
    """Build a RedirectChain from a sequence of (request, response) pairs."""
    hops: List[RedirectHop] = []
    for req, resp in pairs:
        if resp.status_code in REDIRECT_CODES:
            location = None
            for k, v in (resp.headers or {}).items():
                if k.lower() == "location":
                    location = v
                    break
            hops.append(RedirectHop(url=req.url, status_code=resp.status_code, location=location))
    return RedirectChain(hops=hops)
