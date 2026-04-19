"""Tests for req_replay.boundary."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from req_replay.boundary import analyze_boundaries, BoundaryResult, _is_internal
from req_replay.models import CapturedRequest


def _req(url: str, method: str = "GET") -> CapturedRequest:
    r = MagicMock(spec=CapturedRequest)
    r.id = "test-id"
    r.url = url
    r.method = method
    return r


def test_empty_list_returns_clean():
    result = analyze_boundaries([])
    assert result.passed()
    assert result.summary() == "OK – no boundary issues detected"


def test_https_get_external_is_clean():
    result = analyze_boundaries([_req("https://api.example.com/data", "GET")])
    assert result.passed()


def test_http_url_flagged_b001():
    result = analyze_boundaries([_req("http://api.example.com/data", "GET")])
    assert not result.passed()
    codes = [w.code for w in result.warnings]
    assert "B001" in codes


def test_external_mutating_post_flagged_b002():
    result = analyze_boundaries([_req("https://api.example.com/users", "POST")])
    codes = [w.code for w in result.warnings]
    assert "B002" in codes


def test_external_put_flagged():
    result = analyze_boundaries([_req("https://api.example.com/users/1", "PUT")])
    codes = [w.code for w in result.warnings]
    assert "B002" in codes


def test_internal_post_not_flagged_b002():
    result = analyze_boundaries([_req("https://service.internal/users", "POST")])
    codes = [w.code for w in result.warnings]
    assert "B002" not in codes


def test_is_internal_local_suffix():
    assert _is_internal("service.local")


def test_is_internal_private_ip():
    assert _is_internal("192.168.1.1")


def test_is_not_internal_public():
    assert not _is_internal("api.example.com")


def test_display_contains_warning_details():
    result = analyze_boundaries([_req("http://api.example.com/data", "GET")])
    display = result.display()
    assert "B001" in display
    assert "http://api.example.com/data" in display


def test_summary_shows_count():
    result = analyze_boundaries([_req("http://api.example.com/data", "POST")])
    assert "warning" in result.summary()


def test_to_dict_has_expected_keys():
    result = analyze_boundaries([_req("http://api.example.com/", "GET")])
    w = result.warnings[0].to_dict()
    assert set(w.keys()) == {"request_id", "url", "code", "message"}
