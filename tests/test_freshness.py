"""Tests for req_replay.freshness."""
from __future__ import annotations
import pytest
from req_replay.models import CapturedResponse
from req_replay.freshness import analyze_freshness, _parse_max_age


def _resp(headers: dict[str, str], status: int = 200) -> CapturedResponse:
    return CapturedResponse(status_code=status, headers=headers, body=None)


def test_parse_max_age_present():
    assert _parse_max_age("public, max-age=3600") == 3600


def test_parse_max_age_missing():
    assert _parse_max_age("no-cache") is None


def test_parse_max_age_invalid():
    assert _parse_max_age("max-age=abc") is None


def test_fresh_response():
    resp = _resp({"Cache-Control": "max-age=600", "Age": "100"})
    result = analyze_freshness("r1", resp)
    assert result.max_age == 600
    assert result.age == 100
    assert result.ttl == 500
    assert not result.stale
    assert result.warnings == []


def test_stale_response():
    resp = _resp({"Cache-Control": "max-age=60", "Age": "120"})
    result = analyze_freshness("r2", resp)
    assert result.ttl == -60
    assert result.stale


def test_no_cache_control_warns():
    resp = _resp({})
    result = analyze_freshness("r3", resp)
    assert any("freshness cannot be determined" in w for w in result.warnings)


def test_no_cache_directive_marks_stale():
    resp = _resp({"Cache-Control": "no-cache"})
    result = analyze_freshness("r4", resp)
    assert result.stale


def test_no_store_marks_stale():
    resp = _resp({"Cache-Control": "no-store"})
    result = analyze_freshness("r5", resp)
    assert result.stale


def test_missing_age_header_ttl_none():
    resp = _resp({"Cache-Control": "max-age=300"})
    result = analyze_freshness("r6", resp)
    assert result.age is None
    assert result.ttl is None
    assert not result.stale


def test_invalid_age_header_warns():
    resp = _resp({"Cache-Control": "max-age=300", "Age": "not-a-number"})
    result = analyze_freshness("r7", resp)
    assert any("Age header" in w for w in result.warnings)


def test_display_contains_key_fields():
    resp = _resp({"Cache-Control": "max-age=120", "Age": "30"})
    result = analyze_freshness("r8", resp)
    out = result.display()
    assert "r8" in out
    assert "120" in out
    assert "30" in out
    assert "90" in out
    assert "no" in out
