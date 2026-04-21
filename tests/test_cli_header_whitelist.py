"""CLI tests for header-whitelist commands."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from req_replay.cli_header_whitelist import header_whitelist_group
from req_replay.models import CapturedRequest
from req_replay.storage import RequestStore


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def store_path(tmp_path) -> str:
    return str(tmp_path / "store")


def _make_request(
    store_path: str,
    req_id: str = "r1",
    headers: dict[str, str] | None = None,
) -> CapturedRequest:
    store = RequestStore(store_path)
    req = CapturedRequest(
        id=req_id,
        method="GET",
        url="https://example.com/api",
        headers=headers or {},
        body=None,
        timestamp="2024-01-01T00:00:00Z",
        tags=[],
        metadata={},
    )
    store.save(req)
    return req


def test_check_missing_request_shows_error(runner, store_path):
    result = runner.invoke(header_whitelist_group, ["check", "missing", store_path])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_check_clean_request_shows_ok(runner, store_path):
    _make_request(store_path, headers={"Content-Type": "application/json"})
    result = runner.invoke(header_whitelist_group, ["check", "r1", store_path])
    assert result.exit_code == 0
    assert "OK" in result.output


def test_check_forbidden_header_shows_fail(runner, store_path):
    _make_request(store_path, headers={"X-Forbidden": "bad"})
    result = runner.invoke(header_whitelist_group, ["check", "r1", store_path])
    assert result.exit_code == 0  # check does not exit non-zero on warnings
    assert "HW001" in result.output


def test_check_extra_allow_accepts_custom_header(runner, store_path):
    _make_request(store_path, headers={"x-custom": "ok"})
    result = runner.invoke(
        header_whitelist_group, ["check", "r1", store_path, "--allow", "x-custom"]
    )
    assert "OK" in result.output


def test_scan_no_requests_shows_message(runner, store_path):
    result = runner.invoke(header_whitelist_group, ["scan", store_path])
    assert result.exit_code == 0
    assert "no requests" in result.output.lower()


def test_scan_all_clean_exits_zero(runner, store_path):
    _make_request(store_path, headers={"Host": "example.com"}, req_id="r1")
    result = runner.invoke(header_whitelist_group, ["scan", store_path])
    assert result.exit_code == 0


def test_scan_with_violations_exits_nonzero(runner, store_path):
    _make_request(store_path, headers={"X-Bad": "val"}, req_id="r1")
    result = runner.invoke(header_whitelist_group, ["scan", store_path])
    assert result.exit_code != 0
    assert "HW001" in result.output


def test_scan_fail_fast_stops_early(runner, store_path):
    _make_request(store_path, headers={"X-Bad": "val"}, req_id="r1")
    _make_request(store_path, headers={"X-Also-Bad": "val"}, req_id="r2")
    result = runner.invoke(header_whitelist_group, ["scan", store_path, "--fail-fast"])
    assert result.exit_code != 0
