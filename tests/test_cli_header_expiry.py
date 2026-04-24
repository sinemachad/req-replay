"""Tests for req_replay.cli_header_expiry."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import pytest
from click.testing import CliRunner

from req_replay.cli_header_expiry import header_expiry_group
from req_replay.models import CapturedRequest
from req_replay.storage import RequestStore


def _make_request(req_id: str, headers: dict | None = None) -> CapturedRequest:
    return CapturedRequest(
        id=req_id,
        method="GET",
        url="https://example.com/",
        headers=headers or {},
        body=None,
        timestamp="2024-01-01T00:00:00Z",
    )


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def store_path(tmp_path):
    return str(tmp_path / "store")


def _populate(store_path: str, headers: dict | None = None) -> str:
    store = RequestStore(store_path)
    req = _make_request("req-abc", headers=headers)
    store.save(req)
    return "req-abc"


def test_check_missing_request_shows_error(runner, store_path):
    result = runner.invoke(header_expiry_group, ["check", "no-such-id", "--store", store_path])
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "not found" in (result.stderr or "").lower()


def test_check_clean_request_exits_zero(runner, store_path):
    _populate(store_path)
    result = runner.invoke(header_expiry_group, ["check", "req-abc", "--store", store_path])
    assert result.exit_code == 0
    assert "OK" in result.output


def test_scan_no_requests_outputs_message(runner, store_path):
    result = runner.invoke(header_expiry_group, ["scan", "--store", store_path])
    assert result.exit_code == 0
    assert "No requests" in result.output


def test_scan_clean_requests_exits_zero(runner, store_path):
    _populate(store_path)
    result = runner.invoke(header_expiry_group, ["scan", "--store", store_path])
    assert result.exit_code == 0


def test_scan_with_expired_header_exits_nonzero(runner, store_path):
    past = format_datetime(
        datetime.now(tz=timezone.utc) - timedelta(hours=1), usegmt=True
    )
    _populate(store_path, headers={"Expires": past})
    result = runner.invoke(header_expiry_group, ["scan", "--store", store_path])
    assert result.exit_code != 0
