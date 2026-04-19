"""Tests for req_replay.anomaly."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from req_replay.models import CapturedRequest
from req_replay.anomaly import analyze_anomalies, AnomalyResult


def _req(body: str = "", headers: dict | None = None, req_id: str = "r1") -> CapturedRequest:
    return CapturedRequest(
        id=req_id,
        method="POST",
        url="https://example.com/api",
        headers=headers or {"Content-Type": "application/json"},
        body=body,
        timestamp=datetime.now(timezone.utc).isoformat(),
        tags=[],
        metadata={},
    )


def test_fewer_than_three_requests_returns_clean():
    result = analyze_anomalies([_req("x"), _req("y")])
    assert result.passed
    assert result.warnings == []


def test_uniform_bodies_no_anomaly():
    reqs = [_req("hello", req_id=str(i)) for i in range(5)]
    result = analyze_anomalies(reqs)
    assert result.passed


def test_outlier_body_size_flagged():
    reqs = [
        _req("hi", req_id="1"),
        _req("hi", req_id="2"),
        _req("hi", req_id="3"),
        _req("hi", req_id="4"),
        _req("x" * 10_000, req_id="outlier"),
    ]
    result = analyze_anomalies(reqs, z_threshold=2.0)
    ids = [w.request_id for w in result.warnings]
    assert "outlier" in ids


def test_outlier_not_flagged_at_high_threshold():
    reqs = [
        _req("hi", req_id="1"),
        _req("hi", req_id="2"),
        _req("hi", req_id="3"),
        _req("hi", req_id="4"),
        _req("x" * 10_000, req_id="outlier"),
    ]
    result = analyze_anomalies(reqs, z_threshold=100.0)
    assert result.passed


def test_header_count_outlier_flagged():
    normal_headers = {"A": "1"}
    many_headers = {f"H{i}": str(i) for i in range(50)}
    reqs = [
        _req(headers=normal_headers, req_id="1"),
        _req(headers=normal_headers, req_id="2"),
        _req(headers=normal_headers, req_id="3"),
        _req(headers=normal_headers, req_id="4"),
        _req(headers=many_headers, req_id="heavy"),
    ]
    result = analyze_anomalies(reqs, z_threshold=1.5)
    ids = [w.request_id for w in result.warnings]
    assert "heavy" in ids


def test_summary_no_anomalies():
    reqs = [_req("ok", req_id=str(i)) for i in range(4)]
    result = analyze_anomalies(reqs)
    assert "No anomalies" in result.summary()


def test_summary_with_anomalies():
    reqs = [
        _req("hi", req_id="1"),
        _req("hi", req_id="2"),
        _req("hi", req_id="3"),
        _req("hi", req_id="4"),
        _req("x" * 10_000, req_id="outlier"),
    ]
    result = analyze_anomalies(reqs, z_threshold=2.0)
    s = result.summary()
    assert "Anomalies" in s
    assert "body_size" in s


def test_warning_to_dict():
    reqs = [
        _req("hi", req_id="1"),
        _req("hi", req_id="2"),
        _req("hi", req_id="3"),
        _req("hi", req_id="4"),
        _req("x" * 10_000, req_id="outlier"),
    ]
    result = analyze_anomalies(reqs, z_threshold=2.0)
    for w in result.warnings:
        d = w.to_dict()
        assert "request_id" in d
        assert "field" in d
        assert "message" in d
