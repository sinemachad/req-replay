"""Cookie extraction and analysis for captured requests."""
from __future__ import annotations

from dataclasses import dataclass, field
from http.cookies import SimpleCookie
from typing import Dict, List

from req_replay.models import CapturedRequest


@dataclass
class CookieSummary:
    names: List[str] = field(default_factory=list)
    values: Dict[str, str] = field(default_factory=dict)
    count: int = 0

    def display(self) -> str:
        if not self.names:
            return "No cookies found."
        lines = [f"Cookies ({self.count}):"]
        for name in self.names:
            lines.append(f"  {name}={self.values[name]}")
        return "\n".join(lines)


def extract_cookies(request: CapturedRequest) -> Dict[str, str]:
    """Parse the Cookie header from a request and return name→value mapping."""
    cookie_header = ""
    for key, value in request.headers.items():
        if key.lower() == "cookie":
            cookie_header = value
            break

    if not cookie_header:
        return {}

    sc: SimpleCookie = SimpleCookie()
    try:
        sc.load(cookie_header)
    except Exception:
        return {}

    return {k: v.value for k, v in sc.items()}


def filter_cookies(requests: List[CapturedRequest], name: str) -> Dict[str, List[str]]:
    """Find all values seen for a specific cookie name across requests.

    Returns a mapping of request URL to the cookie value observed, only
    including requests where the cookie was present.
    """
    result: Dict[str, List[str]] = {}
    for req in requests:
        cookies = extract_cookies(req)
        if name in cookies:
            result.setdefault(req.url, []).append(cookies[name])
    return result


def summarize_cookies(requests: List[CapturedRequest]) -> CookieSummary:
    """Aggregate cookie names seen across a list of requests."""
    name_set: Dict[str, str] = {}
    for req in requests:
        cookies = extract_cookies(req)
        name_set.update(cookies)

    names = sorted(name_set.keys())
    return CookieSummary(names=names, values=name_set, count=len(names))
