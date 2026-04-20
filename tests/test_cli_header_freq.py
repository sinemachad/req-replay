"""CLI tests for header-freq commands."""
from __future__ import annotations

import os
import pytest
from click.testing import CliRunner

from req_replay.cli_header_freq import header_freq_group
from req_replay.models import CapturedRequest
from req_replay.storage import RequestStore


def _make_request(req_id: str, headers: dict) -> CapturedRequest:
    return CapturedRequest(
        id=req_id,
        method="GET",
        url="https://example.com/",
        headers=headers,
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def store_path(tmp_path):
    return str(tmp_path / "store")


def _populate(store_path: str, requests) -> None:
    s = RequestStore(store_path)
    for req in requests:
        s.save(req)


def test_analyze_no_requests(runner, store_path):
    result = runner.invoke(header_freq_group, ["analyze", "--store", store_path])
    assert result.exit_code == 0
    assert "No requests found" in result.output


def test_analyze_shows_header_counts(runner, store_path):
    _populate(store_path, [
        _make_request("r1", {"Authorization": "Bearer tok", "Accept": "*/*"}),
        _make_request("r2", {"Authorization": "Bearer tok2"}),
    ])
    result = runner.invoke(header_freq_group, ["analyze", "--store", store_path])
    assert result.exit_code == 0
    assert "authorization" in result.output
    assert "2" in result.output


def test_analyze_top_limits_output(runner, store_path):
    headers = {f"x-header-{i}": str(i) for i in range(20)}
    _populate(store_path, [_make_request("r1", headers)])
    result = runner.invoke(header_freq_group, ["analyze", "--store", store_path, "--top", "3"])
    assert result.exit_code == 0
    # Only 3 headers should be listed (plus the summary line)
    lines = [l for l in result.output.splitlines() if l.strip().startswith("x-header")]
    assert len(lines) <= 3


def test_values_no_requests(runner, store_path):
    result = runner.invoke(header_freq_group, ["values", "accept", "--store", store_path])
    assert result.exit_code == 0
    assert "No requests found" in result.output


def test_values_shows_top_values(runner, store_path):
    _populate(store_path, [
        _make_request("r1", {"accept": "application/json"}),
        _make_request("r2", {"accept": "application/json"}),
        _make_request("r3", {"accept": "text/html"}),
    ])
    result = runner.invoke(header_freq_group, ["values", "accept", "--store", store_path])
    assert result.exit_code == 0
    assert "application/json" in result.output
    assert "2" in result.output


def test_values_unknown_header_shows_no_data(runner, store_path):
    _populate(store_path, [_make_request("r1", {"content-type": "application/json"})])
    result = runner.invoke(header_freq_group, ["values", "x-missing", "--store", store_path])
    assert result.exit_code == 0
    assert "No data" in result.output
