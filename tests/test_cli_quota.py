"""Tests for req_replay.cli_quota."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from req_replay.cli_quota import quota_group
from req_replay.models import CapturedRequest
from req_replay.storage import RequestStore


def _make_request(req_id: str = "r1") -> CapturedRequest:
    return CapturedRequest(
        id=req_id,
        method="GET",
        url="https://example.com/",
        headers={},
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


def _populate(store_path: str, req: CapturedRequest, times: int = 1) -> None:
    store = RequestStore(store_path)
    for _ in range(times):
        store.save(req)


def test_analyze_no_requests(runner, store_path):
    result = runner.invoke(quota_group, ["analyze", "--store", store_path])
    assert result.exit_code == 0
    assert "No requests found" in result.output


def test_analyze_shows_pass(runner, store_path):
    _populate(store_path, _make_request("r1"), times=1)
    result = runner.invoke(quota_group, ["analyze", "--store", store_path, "--limit", "10"])
    assert result.exit_code == 0
    assert "PASS" in result.output or "OK" in result.output


def test_analyze_shows_warn_when_over_limit(runner, store_path):
    _populate(store_path, _make_request("r1"), times=5)
    result = runner.invoke(quota_group, ["analyze", "--store", store_path, "--limit", "5"])
    assert result.exit_code == 0
    assert "WARN" in result.output or "Q001" in result.output


def test_check_missing_request_shows_error(runner, store_path):
    result = runner.invoke(quota_group, ["check", "missing-id", "--store", store_path])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_check_existing_request_shows_result(runner, store_path):
    _populate(store_path, _make_request("r1"), times=2)
    result = runner.invoke(quota_group, ["check", "r1", "--store", store_path, "--limit", "10"])
    assert result.exit_code == 0
    assert "r1" in result.output
