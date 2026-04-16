"""Mock server: serve canned responses for captured requests."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from req_replay.models import CapturedRequest, CapturedResponse


@dataclass
class MockRule:
    method: str
    path: str
    response: CapturedResponse
    match_query: bool = False

    def matches(self, method: str, path: str) -> bool:
        return self.method.upper() == method.upper() and self.path == path

    def to_dict(self) -> dict:
        return {
            "method": self.method,
            "path": self.path,
            "match_query": self.match_query,
            "response": self.response.to_dict(),
        }

    @staticmethod
    def from_dict(d: dict) -> "MockRule":
        from req_replay.models import CapturedResponse
        return MockRule(
            method=d["method"],
            path=d["path"],
            response=CapturedResponse.from_dict(d["response"]),
            match_query=d.get("match_query", False),
        )


@dataclass
class MockServer:
    rules: List[MockRule] = field(default_factory=list)

    def add_rule(self, rule: MockRule) -> None:
        self.rules.append(rule)

    def match(self, method: str, path: str) -> Optional[CapturedResponse]:
        for rule in self.rules:
            if rule.matches(method, path):
                return rule.response
        return None

    def rule_count(self) -> int:
        return len(self.rules)


def build_mock_server(pairs: List[tuple]) -> MockServer:
    """Build a MockServer from (CapturedRequest, CapturedResponse) pairs."""
    from urllib.parse import urlparse
    server = MockServer()
    for req, resp in pairs:
        parsed = urlparse(req.url)
        rule = MockRule(method=req.method, path=parsed.path, response=resp)
        server.add_rule(rule)
    return server
