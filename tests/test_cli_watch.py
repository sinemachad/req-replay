"""Tests for req_replay.cli_watch."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from req_replay.cli_watch import watch_group
from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.replay import ReplayResult
from req_replay.watch import WatchEvent


def _make_request() -> CapturedRequest:
    return CapturedRequest(
        id="req-1",
        timestamp=datetime.utcnow().isoformat(),
        method="GET",
        url="http://example.com/",
        headers={},
        body=None,
        tags=[],
    )


def _make_event(passed: bool, iteration: int = 1) -> WatchEvent:
    resp = CapturedResponse(status_code=200 if passed else 500, headers={}, body=b"")
    original = CapturedResponse(status_code=200, headers={}, body=b"")
    result = ReplayResult(original=original, replayed=resp)
    return WatchEvent(timestamp=datetime.utcnow(), result=result, iteration=iteration)


@pytest.fixture()
def runner():
    return CliRunner()


def test_missing_request_shows_error(runner, tmp_path):
    result = runner.invoke(watch_group, ["run", "no-such-id", "--store-dir", str(tmp_path)])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


@patch("req_replay.cli_watch.watch_request")
@patch("req_replay.cli_watch.RequestStore")
def test_run_watch_calls_watch_request(mock_store_cls, mock_watch, runner, tmp_path):
    mock_store = MagicMock()
    mock_store.load.return_value = _make_request()
    mock_store_cls.return_value = mock_store
    mock_watch.return_value = [_make_event(True, 1)]

    result = runner.invoke(
        watch_group,
        ["run", "req-1", "--store-dir", str(tmp_path), "--max", "1", "--interval", "0"],
    )
    assert result.exit_code == 0
    mock_watch.assert_called_once()


@patch("req_replay.cli_watch.watch_request")
@patch("req_replay.cli_watch.RequestStore")
def test_run_watch_summary_line(mock_store_cls, mock_watch, runner, tmp_path):
    mock_store = MagicMock()
    mock_store.load.return_value = _make_request()
    mock_store_cls.return_value = mock_store
    mock_watch.return_value = [_make_event(True, 1), _make_event(True, 2)]

    result = runner.invoke(
        watch_group,
        ["run", "req-1", "--store-dir", str(tmp_path), "--max", "2", "--interval", "0"],
    )
    assert "2/2 passed" in result.output


@patch("req_replay.cli_watch.watch_request")
@patch("req_replay.cli_watch.RequestStore")
def test_run_watch_passes_ignore_headers(mock_store_cls, mock_watch, runner, tmp_path):
    mock_store = MagicMock()
    mock_store.load.return_value = _make_request()
    mock_store_cls.return_value = mock_store
    mock_watch.return_value = [_make_event(True)]

    runner.invoke(
        watch_group,
        [
            "run", "req-1",
            "--store-dir", str(tmp_path),
            "--max", "1",
            "--interval", "0",
            "--ignore-header", "Date",
            "--ignore-header", "X-Request-Id",
        ],
    )
    _, kwargs = mock_watch.call_args
    config = mock_watch.call_args[0][1]
    assert "Date" in config.ignore_headers
    assert "X-Request-Id" in config.ignore_headers
