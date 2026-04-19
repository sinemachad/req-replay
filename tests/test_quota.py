"""Tests for req_replay.quota."""
from __future__ import annotations

import pytest

from req_replay.models import CapturedRequest
from req_replay.quota import QuotaResult, QuotaWarning, analyze_quota


def _req(req_id: str = "abc") -> CapturedRequest:
    return CapturedRequest(
        id=req_id,
        method="GET",
        url="https://example.com/api",
        headers={},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


def test_empty_list_returns_no_results():
    assert analyze_quota([]) == []


def test_single_request_under_limit_passes():
    results = analyze_quota([_req("id1")], limit=5)
    assert len(results) == 1
    assert results[0].passed()
    assert results[0].call_count == 1


def test_request_at_limit_warns():
    reqs = [_req("id1")] * 10
    results = analyze_quota(reqs, limit=10)
    assert len(results) == 1
    result = results[0]
    assert not result.passed()
    assert len(result.warnings) == 1
    assert result.warnings[0].code == "Q001"


def test_request_over_limit_warns():
    reqs = [_req("id1")] * 15
    results = analyze_quota(reqs, limit=10)
    assert not results[0].passed()


def test_multiple_ids_tracked_independently():
    reqs = [_req("a")] * 3 + [_req("b")] * 12
    results = analyze_quota(reqs, limit=10)
    by_id = {r.request_id: r for r in results}
    assert by_id["a"].passed()
    assert not by_id["b"].passed()


def test_summary_ok_message():
    result = QuotaResult(request_id="x", call_count=3, limit=100, warnings=[])
    assert "OK" in result.summary()


def test_summary_warning_message():
    w = QuotaWarning(code="Q001", message="over limit")
    result = QuotaResult(request_id="x", call_count=100, limit=100, warnings=[w])
    assert "warning" in result.summary()


def test_to_dict_structure():
    w = QuotaWarning(code="Q001", message="msg")
    d = w.to_dict()
    assert d["code"] == "Q001"
    assert d["message"] == "msg"
