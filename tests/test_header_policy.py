"""Tests for req_replay.header_policy."""
from __future__ import annotations

import pytest

from req_replay.header_policy import (
    HeaderPolicyResult,
    check_header_policy,
    scan_header_policy,
)
from req_replay.models import CapturedRequest


def _req(
    headers: dict | None = None,
    req_id: str = "req-1",
) -> CapturedRequest:
    return CapturedRequest(
        id=req_id,
        method="GET",
        url="https://example.com/api",
        headers=headers or {},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


# ---------------------------------------------------------------------------
# check_header_policy
# ---------------------------------------------------------------------------

def test_clean_request_passes():
    req = _req(headers={"user-agent": "test/1", "accept": "*/*"})
    result = check_header_policy(req)
    assert result.passed()
    assert result.warnings == []


def test_missing_required_header_hp001():
    req = _req(headers={"user-agent": "test/1"})  # missing 'accept'
    result = check_header_policy(req)
    assert not result.passed()
    codes = [w.code for w in result.warnings]
    assert "HP001" in codes


def test_forbidden_header_hp002():
    req = _req(headers={"user-agent": "ua", "accept": "*/*", "x-debug-token": "secret"})
    result = check_header_policy(req)
    assert not result.passed()
    codes = [w.code for w in result.warnings]
    assert "HP002" in codes


def test_both_violations_reported():
    req = _req(headers={"x-internal-secret": "leak"})  # missing required + has forbidden
    result = check_header_policy(req)
    codes = [w.code for w in result.warnings]
    assert codes.count("HP001") == 2  # user-agent and accept missing
    assert "HP002" in codes


def test_custom_required_headers():
    req = _req(headers={"authorization": "Bearer tok"})
    result = check_header_policy(req, required=["authorization"], forbidden=[])
    assert result.passed()


def test_custom_forbidden_headers():
    req = _req(headers={"x-custom-secret": "val", "user-agent": "ua", "accept": "*/*"})
    result = check_header_policy(req, required=[], forbidden=["x-custom-secret"])
    assert not result.passed()
    assert result.warnings[0].code == "HP002"
    assert result.warnings[0].header == "x-custom-secret"


def test_header_matching_is_case_insensitive():
    req = _req(headers={"User-Agent": "ua", "Accept": "*/*"})  # mixed case
    result = check_header_policy(req)
    assert result.passed()


def test_summary_ok_when_passed():
    req = _req(headers={"user-agent": "ua", "accept": "*/*"})
    result = check_header_policy(req)
    assert "OK" in result.summary()


def test_summary_contains_count_when_failed():
    req = _req(headers={})
    result = check_header_policy(req)
    assert str(len(result.warnings)) in result.summary()


def test_to_dict_structure():
    req = _req(headers={})
    result = check_header_policy(req)
    d = result.to_dict()
    assert "request_id" in d
    assert "passed" in d
    assert "warnings" in d
    assert isinstance(d["warnings"], list)


# ---------------------------------------------------------------------------
# scan_header_policy
# ---------------------------------------------------------------------------

def test_scan_returns_one_result_per_request():
    reqs = [_req(req_id=f"r{i}", headers={"user-agent": "ua", "accept": "*/*"}) for i in range(3)]
    results = scan_header_policy(reqs)
    assert len(results) == 3


def test_scan_empty_list_returns_empty():
    results = scan_header_policy([])
    assert results == []
