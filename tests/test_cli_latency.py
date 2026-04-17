"""Tests for req_replay.cli_latency."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from req_replay.cli_latency import latency_group
from req_replay.storage import RequestStore
from req_replay.models import CapturedRequest


def _make_request(rid: str, duration_ms: float) -> CapturedRequest:
    return CapturedRequest(
        id=rid,
        method="GET",
        url="http://example.com/api",
        headers={},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={"duration_ms": duration_ms},
    )


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def store_path(tmp_path):
    return str(tmp_path)


def _populate(store_path: str, durations) -> None:
    store = RequestStore(Path(store_path))
    for i, d in enumerate(durations):
        store.save(_make_request(f"r{i}", d))


def test_stats_no_requests(runner, store_path):
    result = runner.invoke(latency_group, ["stats", "--store", store_path])
    assert result.exit_code == 0
    assert "No duration_ms" in result.output


def test_stats_shows_min_max(runner, store_path):
    _populate(store_path, [10.0, 50.0, 90.0])
    result = runner.invoke(latency_group, ["stats", "--store", store_path])
    assert result.exit_code == 0
    assert "10.0" in result.output
    assert "90.0" in result.output


def test_stats_shows_mean(runner, store_path):
    _populate(store_path, [20.0, 40.0])
    result = runner.invoke(latency_group, ["stats", "--store", store_path])
    assert "30.0" in result.output


def test_histogram_no_requests(runner, store_path):
    result = runner.invoke(latency_group, ["histogram", "--store", store_path])
    assert result.exit_code == 0
    assert "No duration_ms" in result.output


def test_histogram_renders_buckets(runner, store_path):
    _populate(store_path, [10.0, 30.0, 50.0, 70.0, 90.0])
    result = runner.invoke(
        latency_group, ["histogram", "--store", store_path, "--buckets", "5"]
    )
    assert result.exit_code == 0
    assert "ms |" in result.output
