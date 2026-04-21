"""Tests for req_replay.cli_header_diff."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from req_replay.cli_header_diff import header_diff_group
from req_replay.models import CapturedRequest
from req_replay.storage import RequestStore


def _make_request(id_: str, headers: dict) -> CapturedRequest:
    return CapturedRequest(
        id=id_,
        method="GET",
        url="https://example.com/",
        headers=headers,
        body=None,
        metadata={},
        tags=[],
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


def test_compare_missing_first_request_shows_error(runner, store_path):
    result = runner.invoke(
        header_diff_group,
        ["compare", "missing-a", "missing-b", "--store", store_path],
    )
    assert result.exit_code != 0
    assert "not found" in result.output


def test_compare_missing_second_request_shows_error(runner, store_path):
    req_a = _make_request("aaa", {"Accept": "*/*"})
    _populate(store_path, req_a)
    result = runner.invoke(
        header_diff_group,
        ["compare", "aaa", "missing-b", "--store", store_path],
    )
    assert result.exit_code != 0
    assert "not found" in result.output


def test_compare_identical_headers(runner, store_path):
    req_a = _make_request("aaa", {"Accept": "application/json"})
    req_b = _make_request("bbb", {"Accept": "application/json"})
    _populate(store_path, req_a, req_b)
    result = runner.invoke(
        header_diff_group,
        ["compare", "aaa", "bbb", "--store", store_path],
    )
    assert result.exit_code == 0
    assert "identical" in result.output.lower()


def test_compare_shows_added_header(runner, store_path):
    req_a = _make_request("aaa", {"Accept": "*/*"})
    req_b = _make_request("bbb", {"Accept": "*/*", "X-Extra": "yes"})
    _populate(store_path, req_a, req_b)
    result = runner.invoke(
        header_diff_group,
        ["compare", "aaa", "bbb", "--store", store_path],
    )
    assert result.exit_code == 0
    assert "x-extra" in result.output
    assert "+" in result.output


def test_compare_shows_removed_header(runner, store_path):
    req_a = _make_request("aaa", {"Accept": "*/*", "X-Gone": "bye"})
    req_b = _make_request("bbb", {"Accept": "*/*"})
    _populate(store_path, req_a, req_b)
    result = runner.invoke(
        header_diff_group,
        ["compare", "aaa", "bbb", "--store", store_path],
    )
    assert result.exit_code == 0
    assert "x-gone" in result.output


def test_compare_ignore_flag_suppresses_header(runner, store_path):
    req_a = _make_request("aaa", {"Accept": "*/*", "X-Request-Id": "111"})
    req_b = _make_request("bbb", {"Accept": "*/*", "X-Request-Id": "222"})
    _populate(store_path, req_a, req_b)
    result = runner.invoke(
        header_diff_group,
        ["compare", "aaa", "bbb", "--store", store_path, "--ignore", "X-Request-Id"],
    )
    assert result.exit_code == 0
    assert "identical" in result.output.lower()
