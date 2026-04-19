"""Tests for req_replay.version_drift."""
import pytest
from req_replay.models import CapturedRequest
from req_replay.version_drift import analyze_version_drift, _extract_version


def _req(
    url: str = "https://api.example.com/v1/users",
    headers: dict | None = None,
    req_id: str = "r1",
) -> CapturedRequest:
    return CapturedRequest(
        id=req_id,
        method="GET",
        url=url,
        headers=headers or {},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


def test_extract_version_from_path():
    req = _req(url="https://api.example.com/v2/items")
    assert _extract_version(req) == "2"


def test_extract_version_from_query_param():
    req = _req(url="https://api.example.com/items?version=3")
    assert _extract_version(req) == "3"


def test_extract_version_from_api_version_query():
    req = _req(url="https://api.example.com/items?api_version=2024-01")
    assert _extract_version(req) == "2024-01"


def test_extract_version_from_header():
    req = _req(
        url="https://api.example.com/items",
        headers={"Api-Version": "5"},
    )
    assert _extract_version(req) == "5"


def test_extract_version_missing_returns_none():
    req = _req(url="https://api.example.com/items")
    assert _extract_version(req) is None


def test_no_warnings_when_all_match():
    reqs = [
        _req(url="https://api.example.com/v1/a", req_id="r1"),
        _req(url="https://api.example.com/v1/b", req_id="r2"),
    ]
    result = analyze_version_drift(reqs, expected_version="1")
    assert result.passed
    assert result.warnings == []


def test_mismatch_generates_warning():
    reqs = [
        _req(url="https://api.example.com/v2/a", req_id="r1"),
    ]
    result = analyze_version_drift(reqs, expected_version="1")
    assert not result.passed
    assert len(result.warnings) == 1
    w = result.warnings[0]
    assert w.detected_version == "2"
    assert w.expected_version == "1"
    assert w.request_id == "r1"


def test_missing_version_generates_warning():
    reqs = [_req(url="https://api.example.com/items", req_id="r99")]
    result = analyze_version_drift(reqs, expected_version="1")
    assert not result.passed
    assert result.warnings[0].detected_version is None


def test_summary_clean():
    result = analyze_version_drift([], expected_version="1")
    assert "No version drift" in result.summary()


def test_summary_with_warnings():
    reqs = [_req(url="https://api.example.com/v3/x", req_id="r1")]
    result = analyze_version_drift(reqs, expected_version="1")
    s = result.summary()
    assert "drift" in s.lower()
    assert "r1" in s


def test_warning_to_dict():
    reqs = [_req(url="https://api.example.com/v9/x", req_id="abc")]
    result = analyze_version_drift(reqs, expected_version="1")
    d = result.warnings[0].to_dict()
    assert d["request_id"] == "abc"
    assert d["detected_version"] == "9"
    assert d["expected_version"] == "1"
