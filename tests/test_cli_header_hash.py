"""Tests for req_replay.cli_header_hash."""
from __future__ import annotations

import os

import pytest
from click.testing import CliRunner

from req_replay.cli_header_hash import header_hash_group
from req_replay.models import CapturedRequest
from req_replay.storage import RequestStore


def _make_request(rid: str = "abc123", headers: dict | None = None) -> CapturedRequest:
    return CapturedRequest(
        id=rid,
        method="GET",
        url="https://example.com",
        headers=headers or {"Accept": "application/json"},
        body=None,
        timestamp="2024-01-01T00:00:00Z",
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
    for r in requests:
        store.save(r)


def test_show_missing_request_shows_error(runner, store_path):
    result = runner.invoke(
        header_hash_group, ["show", "nope", "--store", store_path]
    )
    assert result.exit_code != 0
    assert "not found" in result.output


def test_show_displays_digest(runner, store_path):
    req = _make_request()
    _populate(store_path, req)
    result = runner.invoke(
        header_hash_group, ["show", req.id, "--store", store_path]
    )
    assert result.exit_code == 0
    assert "sha256" in result.output
    assert "Digest" in result.output


def test_show_invalid_algo_shows_error(runner, store_path):
    req = _make_request()
    _populate(store_path, req)
    result = runner.invoke(
        header_hash_group, ["show", req.id, "--store", store_path, "--algo", "blake2b"]
    )
    assert result.exit_code != 0
    assert "Error" in result.output


def test_compare_identical_headers_shows_match(runner, store_path):
    r1 = _make_request("r1", {"X-A": "same"})
    r2 = _make_request("r2", {"X-A": "same"})
    _populate(store_path, r1, r2)
    result = runner.invoke(
        header_hash_group, ["compare", "r1", "r2", "--store", store_path]
    )
    assert result.exit_code == 0
    assert "MATCH" in result.output


def test_compare_different_headers_shows_differ(runner, store_path):
    r1 = _make_request("r1", {"X-A": "one"})
    r2 = _make_request("r2", {"X-A": "two"})
    _populate(store_path, r1, r2)
    result = runner.invoke(
        header_hash_group, ["compare", "r1", "r2", "--store", store_path]
    )
    assert result.exit_code == 0
    assert "DIFFER" in result.output


def test_compare_missing_request_shows_error(runner, store_path):
    r1 = _make_request("r1")
    _populate(store_path, r1)
    result = runner.invoke(
        header_hash_group, ["compare", "r1", "ghost", "--store", store_path]
    )
    assert result.exit_code != 0
    assert "not found" in result.output


def test_scan_no_requests_shows_message(runner, store_path):
    result = runner.invoke(
        header_hash_group, ["scan", "--store", store_path]
    )
    assert result.exit_code == 0
    assert "No requests" in result.output


def test_scan_shows_all_digests(runner, store_path):
    reqs = [_make_request(f"r{i}", {"X-N": str(i)}) for i in range(3)]
    _populate(store_path, *reqs)
    result = runner.invoke(
        header_hash_group, ["scan", "--store", store_path]
    )
    assert result.exit_code == 0
    for req in reqs:
        assert req.id in result.output
