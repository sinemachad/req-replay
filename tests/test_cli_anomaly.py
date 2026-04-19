"""Tests for req_replay.cli_anomaly."""
from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from click.testing import CliRunner

from req_replay.cli_anomaly import anomaly_group
from req_replay.storage import RequestStore
from req_replay.models import CapturedRequest


def _make_request(req_id: str, body: str = "hello") -> CapturedRequest:
    return CapturedRequest(
        id=req_id,
        method="POST",
        url="https://example.com/api",
        headers={"Content-Type": "application/json"},
        body=body,
        timestamp=datetime.now(timezone.utc).isoformat(),
        tags=[],
        metadata={},
    )


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def store_path(tmp_path):
    return str(tmp_path / "store")


def _populate(store_path: str, bodies: list[str]) -> list[str]:
    store = RequestStore(store_path)
    ids = []
    for i, body in enumerate(bodies):
        req = _make_request(str(i), body)
        store.save(req)
        ids.append(req.id)
    return ids


def test_scan_no_requests(runner, store_path):
    result = runner.invoke(anomaly_group, ["scan", "--store", store_path])
    assert result.exit_code == 0
    assert "No requests" in result.output


def test_scan_clean_store(runner, store_path):
    _populate(store_path, ["hi", "hi", "hi", "hi"])
    result = runner.invoke(anomaly_group, ["scan", "--store", store_path])
    assert result.exit_code == 0
    assert "No anomalies" in result.output


def test_scan_detects_outlier(runner, store_path):
    _populate(store_path, ["hi", "hi", "hi", "hi", "x" * 10_000])
    result = runner.invoke(
        anomaly_group, ["scan", "--store", store_path, "--threshold", "2.0"]
    )
    assert result.exit_code == 1
    assert "body_size" in result.output


def test_check_missing_request(runner, store_path):
    result = runner.invoke(
        anomaly_group, ["check", "ghost", "--store", store_path]
    )
    assert result.exit_code == 1
    assert "not found" in result.output


def test_check_clean_request(runner, store_path):
    ids = _populate(store_path, ["hi", "hi", "hi", "hi"])
    result = runner.invoke(
        anomaly_group, ["check", ids[0], "--store", store_path]
    )
    assert result.exit_code == 0
    assert "no anomalies" in result.output
