"""Tests for req_replay.header_deprecation."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from req_replay.header_deprecation import (
    HeaderDeprecationResult,
    check_deprecated_headers,
    scan_deprecated_headers,
)
from req_replay.models import CapturedRequest


def _req(headers: dict | None = None) -> CapturedRequest:
    return CapturedRequest(
        id="test-id",
        method="GET",
        url="https://example.com/api",
        headers=headers or {},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


# ── unit tests ──────────────────────────────────────────────────────────────

def test_clean_request_passes():
    result = check_deprecated_headers(_req({"Content-Type": "application/json"}))
    assert result.passed


def test_clean_request_summary_ok():
    result = check_deprecated_headers(_req())
    assert "OK" in result.summary()


def test_pragma_header_flagged():
    result = check_deprecated_headers(_req({"Pragma": "no-cache"}))
    assert not result.passed
    assert any(w.header == "Pragma" for w in result.warnings)


def test_pragma_header_code_hd001():
    result = check_deprecated_headers(_req({"Pragma": "no-cache"}))
    assert all(w.code == "HD001" for w in result.warnings)


def test_p3p_header_flagged():
    result = check_deprecated_headers(_req({"P3P": 'CP="NOI"'}))
    assert not result.passed


def test_case_insensitive_matching():
    result = check_deprecated_headers(_req({"pragma": "no-cache"}))
    assert not result.passed


def test_multiple_deprecated_headers_all_reported():
    result = check_deprecated_headers(
        _req({"Pragma": "no-cache", "P3P": 'CP="NOI"', "Expires": "0"})
    )
    assert len(result.warnings) == 3


def test_extra_deprecated_headers_detected():
    result = check_deprecated_headers(
        _req({"X-Legacy-Token": "abc"}),
        extra_deprecated={"x-legacy-token": "Use Authorization instead"},
    )
    assert not result.passed
    assert result.warnings[0].suggestion == "Use Authorization instead"


def test_display_contains_header_name():
    result = check_deprecated_headers(_req({"Pragma": "no-cache"}))
    display = result.display()
    assert "Pragma" in display


def test_display_contains_suggestion():
    result = check_deprecated_headers(_req({"Pragma": "no-cache"}))
    assert "Cache-Control" in result.display()


def test_to_dict_structure():
    result = check_deprecated_headers(_req({"Pragma": "no-cache"}))
    d = result.warnings[0].to_dict()
    assert set(d.keys()) == {"code", "header", "message", "suggestion"}


def test_scan_returns_result_per_request():
    reqs = [_req({"Pragma": "no-cache"}), _req({"Content-Type": "application/json"})]
    results = scan_deprecated_headers(reqs)
    assert len(results) == 2


def test_scan_identifies_only_bad_requests():
    reqs = [_req({"Pragma": "no-cache"}), _req({"Content-Type": "application/json"})]
    results = scan_deprecated_headers(reqs)
    assert not results[0].passed
    assert results[1].passed


def test_request_id_stored_in_result():
    req = _req()
    req.id = "my-id-123"
    result = check_deprecated_headers(req)
    assert result.request_id == "my-id-123"
