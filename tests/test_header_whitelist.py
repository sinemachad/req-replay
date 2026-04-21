"""Tests for req_replay.header_whitelist."""
from __future__ import annotations

import pytest

from req_replay.header_whitelist import (
    WhitelistResult,
    WhitelistWarning,
    _DEFAULT_ALLOWED,
    check_whitelist,
    scan_whitelist,
)
from req_replay.models import CapturedRequest


def _req(headers: dict[str, str] | None = None, req_id: str = "r1") -> CapturedRequest:
    return CapturedRequest(
        id=req_id,
        method="GET",
        url="https://example.com/api",
        headers=headers or {},
        body=None,
        timestamp="2024-01-01T00:00:00Z",
        tags=[],
        metadata={},
    )


# ---------------------------------------------------------------------------
# WhitelistResult helpers
# ---------------------------------------------------------------------------

def test_passed_when_no_warnings():
    result = WhitelistResult(request_id="r1", warnings=[])
    assert result.passed() is True


def test_failed_when_warnings_present():
    result = WhitelistResult(
        request_id="r1",
        warnings=[WhitelistWarning(code="HW001", header="x-custom", message="not allowed")],
    )
    assert result.passed() is False


def test_summary_ok():
    result = WhitelistResult(request_id="r1", warnings=[])
    assert "OK" in result.summary()


def test_summary_fail_contains_code():
    result = WhitelistResult(
        request_id="r1",
        warnings=[WhitelistWarning(code="HW001", header="x-foo", message="msg")],
    )
    assert "HW001" in result.summary()
    assert "FAIL" in result.summary()


def test_to_dict_structure():
    result = WhitelistResult(request_id="r1", warnings=[])
    d = result.to_dict()
    assert d["request_id"] == "r1"
    assert d["passed"] is True
    assert d["warnings"] == []


# ---------------------------------------------------------------------------
# check_whitelist
# ---------------------------------------------------------------------------

def test_clean_request_passes():
    req = _req(headers={"Content-Type": "application/json", "Host": "example.com"})
    result = check_whitelist(req)
    assert result.passed()


def test_unknown_header_flagged_hw001():
    req = _req(headers={"X-Secret-Token": "abc"})
    result = check_whitelist(req)
    assert not result.passed()
    assert result.warnings[0].code == "HW001"
    assert "X-Secret-Token" in result.warnings[0].message


def test_check_case_insensitive_matching():
    req = _req(headers={"content-type": "text/plain"})
    result = check_whitelist(req)
    assert result.passed()


def test_custom_allowed_set_overrides_defaults():
    req = _req(headers={"x-custom": "value"})
    result = check_whitelist(req, allowed=["x-custom"])
    assert result.passed()


def test_strict_mode_only_custom_headers_allowed():
    req = _req(headers={"Content-Type": "application/json"})
    # strict: only allow 'x-custom', so content-type should fail
    result = check_whitelist(req, allowed=["x-custom"])
    assert not result.passed()


def test_empty_headers_passes():
    req = _req(headers={})
    result = check_whitelist(req)
    assert result.passed()


# ---------------------------------------------------------------------------
# scan_whitelist
# ---------------------------------------------------------------------------

def test_scan_empty_list_returns_empty():
    assert scan_whitelist([]) == []


def test_scan_returns_one_result_per_request():
    reqs = [_req(req_id=f"r{i}") for i in range(3)]
    results = scan_whitelist(reqs)
    assert len(results) == 3


def test_scan_mixed_results():
    clean = _req(headers={"Host": "example.com"}, req_id="clean")
    dirty = _req(headers={"X-Forbidden": "val"}, req_id="dirty")
    results = {r.request_id: r for r in scan_whitelist([clean, dirty])}
    assert results["clean"].passed()
    assert not results["dirty"].passed()
