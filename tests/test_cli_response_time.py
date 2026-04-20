"""Tests for req_replay.cli_response_time."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from click.testing import CliRunner

from req_replay.cli_response_time import response_time_group
from req_replay.models import CapturedRequest
from req_replay.storage import RequestStore


def _make_request(req_id: str, duration_ms: float | None = None, method: str = "GET") -> CapturedRequest:
    meta = {"duration_ms": duration_ms} if duration_ms is not None else {}
    return CapturedRequest(
        id=req_id,
        method=method,
        url="https://api.example.com/v1/resource",
        headers={"Accept": "application/json"},
        body=None,
        timestamp=datetime.now(timezone.utc).isoformat(),
        tags=[],
        metadata=meta,
    )


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def store_path(tmp_path: Path) -> Path:
    return tmp_path / "store"


def _populate(store_path: Path, requests):
    store = RequestStore(str(store_path))
    for req in requests:
        store.save(req)


def test_analyze_no_requests(runner, store_path):
    store_path.mkdir()
    result = runner.invoke(response_time_group, ["analyze", "--store", str(store_path)])
    assert result.exit_code == 0
    assert "No requests found" in result.output


def test_analyze_shows_distribution(runner, store_path):
    reqs = [
        _make_request("id-1", 50.0),
        _make_request("id-2", 200.0),
        _make_request("id-3", 1200.0),
    ]
    _populate(store_path, reqs)
    result = runner.invoke(response_time_group, ["analyze", "--store", str(store_path)])
    assert result.exit_code == 0
    assert "<100ms" in result.output
    assert "100-300ms" in result.output
    assert ">1s" in result.output


def test_analyze_filter_by_method(runner, store_path):
    reqs = [
        _make_request("id-1", 50.0, method="GET"),
        _make_request("id-2", 200.0, method="POST"),
    ]
    _populate(store_path, reqs)
    result = runner.invoke(response_time_group, ["analyze", "--store", str(store_path), "--method", "POST"])
    assert result.exit_code == 0
    assert "1 requests" in result.output


def test_slow_no_slow_requests(runner, store_path):
    reqs = [_make_request("id-1", 50.0)]
    _populate(store_path, reqs)
    result = runner.invoke(response_time_group, ["slow", "--store", str(store_path), "--threshold", "500"])
    assert result.exit_code == 0
    assert "No requests exceeded" in result.output


def test_slow_lists_slow_requests(runner, store_path):
    reqs = [
        _make_request("id-slow", 1500.0),
        _make_request("id-fast", 100.0),
    ]
    _populate(store_path, reqs)
    result = runner.invoke(response_time_group, ["slow", "--store", str(store_path), "--threshold", "500"])
    assert result.exit_code == 0
    assert "id-slow" in result.output
    assert "id-fast" not in result.output
