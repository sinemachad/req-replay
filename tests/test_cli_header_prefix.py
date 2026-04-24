"""Tests for req_replay.cli_header_prefix."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from req_replay.cli_header_prefix import header_prefix_group
from req_replay.models import CapturedRequest
from req_replay.storage import RequestStore


def _make_request(request_id: str, headers: dict) -> CapturedRequest:
    return CapturedRequest(
        id=request_id,
        method="GET",
        url="https://example.com/api",
        headers=headers,
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


def _populate(store_path: str, request_id: str, headers: dict) -> None:
    store = RequestStore(store_path)
    store.save(_make_request(request_id, headers))


# ---------------------------------------------------------------------------
# find command
# ---------------------------------------------------------------------------

def test_find_missing_request_shows_error(runner, store_path):
    result = runner.invoke(
        header_prefix_group, ["find", "missing", "x-", "--store", store_path]
    )
    assert result.exit_code == 1
    assert "not found" in result.output.lower() or "not found" in (result.stderr or "")


def test_find_returns_matched_headers(runner, store_path):
    _populate(store_path, "r1", {"x-request-id": "123", "accept": "*/*"})
    result = runner.invoke(
        header_prefix_group, ["find", "r1", "x-", "--store", store_path]
    )
    assert result.exit_code == 0
    assert "x-request-id" in result.output
    assert "accept" not in result.output


def test_find_no_match_shows_message(runner, store_path):
    _populate(store_path, "r2", {"content-type": "application/json"})
    result = runner.invoke(
        header_prefix_group, ["find", "r2", "x-", "--store", store_path]
    )
    assert result.exit_code == 0
    assert "no headers" in result.output.lower()


# ---------------------------------------------------------------------------
# strip command
# ---------------------------------------------------------------------------

def test_strip_missing_request_shows_error(runner, store_path):
    result = runner.invoke(
        header_prefix_group, ["strip", "missing", "x-", "--store", store_path]
    )
    assert result.exit_code == 1


def test_strip_displays_result(runner, store_path):
    _populate(store_path, "r3", {"x-trace": "abc", "accept": "*/*"})
    result = runner.invoke(
        header_prefix_group, ["strip", "r3", "x-", "--store", store_path]
    )
    assert result.exit_code == 0
    assert "x-trace" in result.output


def test_strip_save_persists_changes(runner, store_path):
    _populate(store_path, "r4", {"x-foo": "bar", "accept": "*/*"})
    result = runner.invoke(
        header_prefix_group,
        ["strip", "r4", "x-", "--store", store_path, "--save"],
    )
    assert result.exit_code == 0
    assert "updated" in result.output.lower()
    store = RequestStore(store_path)
    saved = store.load("r4")
    assert "x-foo" not in saved.headers
    assert "accept" in saved.headers


def test_strip_save_no_changes_reports_no_modification(runner, store_path):
    _populate(store_path, "r5", {"accept": "*/*"})
    result = runner.invoke(
        header_prefix_group,
        ["strip", "r5", "x-", "--store", store_path, "--save"],
    )
    assert result.exit_code == 0
    assert "no changes" in result.output.lower()
