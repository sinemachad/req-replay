"""Tests for req_replay.mock."""
from __future__ import annotations

import pytest

from req_replay.mock import MockRule, MockServer, build_mock_server
from req_replay.models import CapturedRequest, CapturedResponse


def _resp(status: int = 200, body: str = "ok") -> CapturedResponse:
    return CapturedResponse(status_code=status, headers={}, body=body, elapsed_ms=10.0)


def _req(method: str = "GET", url: str = "http://example.com/api") -> CapturedRequest:
    return CapturedRequest(method=method, url=url, headers={}, body=None, tags=[])


def test_mock_rule_matches_method_and_path():
    rule = MockRule(method="GET", path="/api", response=_resp())
    assert rule.matches("GET", "/api")


def test_mock_rule_case_insensitive_method():
    rule = MockRule(method="post", path="/submit", response=_resp(201))
    assert rule.matches("POST", "/submit")


def test_mock_rule_no_match_wrong_path():
    rule = MockRule(method="GET", path="/api", response=_resp())
    assert not rule.matches("GET", "/other")


def test_mock_server_match_returns_response():
    server = MockServer()
    resp = _resp(200, "hello")
    server.add_rule(MockRule(method="GET", path="/hello", response=resp))
    result = server.match("GET", "/hello")
    assert result is not None
    assert result.status_code == 200


def test_mock_server_no_match_returns_none():
    server = MockServer()
    assert server.match("GET", "/missing") is None


def test_mock_server_rule_count():
    server = MockServer()
    server.add_rule(MockRule(method="GET", path="/a", response=_resp()))
    server.add_rule(MockRule(method="POST", path="/b", response=_resp(201)))
    assert server.rule_count() == 2


def test_build_mock_server_from_pairs():
    req = _req("GET", "http://example.com/api/users")
    resp = _resp(200, "[]")  
    server = build_mock_server([(req, resp)])
    assert server.rule_count() == 1
    result = server.match("GET", "/api/users")
    assert result is not None
    assert result.body == "[]"


def test_mock_rule_roundtrip():
    rule = MockRule(method="DELETE", path="/item/1", response=_resp(204, ""))
    restored = MockRule.from_dict(rule.to_dict())
    assert restored.method == rule.method
    assert restored.path == rule.path
    assert restored.response.status_code == 204


def test_build_mock_server_multiple_pairs():
    pairs = [
        (_req("GET", "http://a.com/x"), _resp(200)),
        (_req("POST", "http://a.com/y"), _resp(201)),
    ]
    server = build_mock_server(pairs)
    assert server.rule_count() == 2
