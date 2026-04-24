"""Tests for req_replay.cli_header_merge."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from req_replay.cli_header_merge import header_merge_group
from req_replay.models import CapturedRequest
from req_replay.storage import RequestStore


def _make_request(rid: str, headers: dict) -> CapturedRequest:
    return CapturedRequest(
        id=rid,
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


def _populate(store_path: str, *requests: CapturedRequest) -> None:
    store = RequestStore(store_path)
    for req in requests:
        store.save(req)


def test_missing_request_shows_error(runner, store_path):
    result = runner.invoke(header_merge_group, ["run", "nonexistent", "--store", store_path])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_run_merges_headers(runner, store_path):
    r1 = _make_request("r1", {"Accept": "*/*", "X-App": "foo"})
    r2 = _make_request("r2", {"Content-Type": "application/json"})
    _populate(store_path, r1, r2)
    result = runner.invoke(
        header_merge_group, ["run", "r1", "r2", "--store", store_path]
    )
    assert result.exit_code == 0
    assert "2 request" in result.output


def test_run_with_conflict_exits_nonzero(runner, store_path):
    r1 = _make_request("r1", {"Accept": "text/html"})
    r2 = _make_request("r2", {"Accept": "application/json"})
    _populate(store_path, r1, r2)
    result = runner.invoke(
        header_merge_group,
        ["run", "r1", "r2", "--store", store_path, "--strategy", "union"],
    )
    assert result.exit_code != 0


def test_run_strategy_last_no_conflict_exit(runner, store_path):
    r1 = _make_request("r1", {"Accept": "text/html"})
    r2 = _make_request("r2", {"Accept": "text/html"})
    _populate(store_path, r1, r2)
    result = runner.invoke(
        header_merge_group,
        ["run", "r1", "r2", "--store", store_path, "--strategy", "last"],
    )
    assert result.exit_code == 0
    assert "No conflicts" in result.output


def test_run_extra_header_shown(runner, store_path):
    r1 = _make_request("r1", {"Accept": "*/*"})
    _populate(store_path, r1)
    result = runner.invoke(
        header_merge_group,
        ["run", "r1", "--store", store_path, "--extra", "X-Trace-Id=abc"],
    )
    assert result.exit_code == 0
