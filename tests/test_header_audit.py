"""Tests for req_replay.header_audit."""
from __future__ import annotations

import pytest

from req_replay.header_audit import HeaderAuditResult, HeaderAuditWarning, audit_all, audit_headers
from req_replay.models import CapturedRequest


def _req(
    headers: dict | None = None,
    method: str = "GET",
    url: str = "https://example.com/api",
    req_id: str = "req-1",
) -> CapturedRequest:
    return CapturedRequest(
        id=req_id,
        method=method,
        url=url,
        headers=headers or {},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


def test_clean_request_passes():
    req = _req(headers={"content-type": "application/json", "accept": "*/*", "user-agent": "test"})
    result = audit_headers(req)
    assert result.passed
    assert result.warnings == []


def test_clean_request_summary_ok():
    req = _req(headers={"content-type": "application/json", "accept": "*/*", "user-agent": "test"})
    result = audit_headers(req)
    assert "OK" in result.summary


def test_ha001_sensitive_authorization_flagged():
    req = _req(headers={"Authorization": "Bearer secret", "content-type": "application/json", "accept": "*/*", "user-agent": "test"})
    result = audit_headers(req)
    codes = [w.code for w in result.warnings]
    assert "HA001" in codes


def test_ha001_cookie_flagged():
    req = _req(headers={"cookie": "session=abc", "content-type": "text/html", "accept": "*/*", "user-agent": "test"})
    result = audit_headers(req)
    codes = [w.code for w in result.warnings]
    assert "HA001" in codes


def test_ha001_case_insensitive():
    req = _req(headers={"X-API-KEY": "my-key", "content-type": "application/json", "accept": "*/*", "user-agent": "test"})
    result = audit_headers(req)
    codes = [w.code for w in result.warnings]
    assert "HA001" in codes


def test_ha002_missing_content_type_flagged():
    req = _req(headers={"accept": "*/*", "user-agent": "test"})
    result = audit_headers(req)
    codes = [w.code for w in result.warnings]
    assert "HA002" in codes
    headers_warned = [w.header for w in result.warnings if w.code == "HA002"]
    assert "content-type" in headers_warned


def test_ha002_missing_user_agent_flagged():
    req = _req(headers={"content-type": "application/json", "accept": "*/*"})
    result = audit_headers(req)
    codes = [w.code for w in result.warnings]
    assert "HA002" in codes


def test_ha003_empty_header_value_flagged():
    req = _req(headers={"content-type": "", "accept": "*/*", "user-agent": "test"})
    result = audit_headers(req)
    codes = [w.code for w in result.warnings]
    assert "HA003" in codes


def test_summary_contains_count_and_codes():
    req = _req(headers={})
    result = audit_headers(req)
    assert not result.passed
    assert "warning" in result.summary


def test_audit_all_returns_one_result_per_request():
    reqs = [_req(req_id=f"req-{i}") for i in range(3)]
    results = audit_all(reqs)
    assert len(results) == 3
    ids = [r.request_id for r in results]
    assert ids == ["req-0", "req-1", "req-2"]


def test_warning_to_dict():
    w = HeaderAuditWarning(code="HA001", header="authorization", message="test")
    d = w.to_dict()
    assert d["code"] == "HA001"
    assert d["header"] == "authorization"
    assert d["message"] == "test"


def test_audit_all_empty_list():
    results = audit_all([])
    assert results == []
