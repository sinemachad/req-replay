"""Tests for req_replay.header_blacklist."""
from __future__ import annotations

import pytest

from req_replay.header_blacklist import (
    BlacklistResult,
    BlacklistWarning,
    _DEFAULT_BLACKLIST,
    check_blacklist,
    scan_blacklist,
)
from req_replay.models import CapturedRequest


def _req(headers: dict | None = None) -> CapturedRequest:
    return CapturedRequest(
        id="test-id",
        method="GET",
        url="https://example.com/api",
        headers=headers or {},
        body=None,
        timestamp="2024-01-01T00:00:00Z",
    )


def test_clean_request_passes():
    req = _req({"content-type": "application/json", "accept": "*/*"})
    result = check_blacklist(req)
    assert result.passed()


def test_clean_request_summary_ok():
    result = check_blacklist(_req())
    assert "OK" in result.summary()


def test_blacklisted_header_flagged():
    req = _req({"x-forwarded-for": "1.2.3.4"})
    result = check_blacklist(req)
    assert not result.passed()
    assert any(w.code == "BL001" for w in result.warnings)


def test_blacklisted_header_case_insensitive():
    req = _req({"X-Forwarded-For": "1.2.3.4"})
    result = check_blacklist(req)
    assert not result.passed()


def test_multiple_blacklisted_headers_all_flagged():
    req = _req({"x-forwarded-for": "1.2.3.4", "proxy-authorization": "Basic xyz"})
    result = check_blacklist(req)
    assert len(result.warnings) == 2


def test_custom_blacklist_overrides_default():
    req = _req({"x-forwarded-for": "1.2.3.4", "x-custom-bad": "oops"})
    result = check_blacklist(req, blacklist={"x-custom-bad"})
    codes = [w.header.lower() for w in result.warnings]
    assert "x-custom-bad" in codes
    assert "x-forwarded-for" not in codes


def test_empty_blacklist_always_passes():
    req = _req({"x-forwarded-for": "1.2.3.4", "proxy-authorization": "token"})
    result = check_blacklist(req, blacklist=set())
    assert result.passed()


def test_summary_fail_contains_code():
    req = _req({"x-real-ip": "10.0.0.1"})
    result = check_blacklist(req)
    assert "BL001" in result.summary()


def test_to_dict_structure():
    req = _req({"x-real-ip": "10.0.0.1"})
    result = check_blacklist(req)
    d = result.to_dict()
    assert "request_id" in d
    assert "passed" in d
    assert "warnings" in d
    assert d["warnings"][0]["code"] == "BL001"


def test_scan_blacklist_returns_one_result_per_request():
    reqs = [
        _req({"content-type": "application/json"}),
        _req({"x-forwarded-for": "1.2.3.4"}),
    ]
    results = scan_blacklist(reqs)
    assert len(results) == 2
    assert results[0].passed()
    assert not results[1].passed()


def test_scan_empty_list_returns_empty():
    assert scan_blacklist([]) == []


def test_default_blacklist_contains_expected_entries():
    assert "x-forwarded-for" in _DEFAULT_BLACKLIST
    assert "proxy-authorization" in _DEFAULT_BLACKLIST
