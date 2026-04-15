"""Tests for req_replay.cli_retry."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from req_replay.cli_retry import retry_group
from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.replay import ReplayResult
from req_replay.retry import RetryResult


def _make_request() -> CapturedRequest:
    return CapturedRequest(
        id="req-1",
        method="GET",
        url="http://example.com/",
        headers={},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
    )


def _make_retry_result(passed: bool) -> RetryResult:
    original = CapturedResponse(status_code=200, headers={}, body=b"ok")
    replayed = CapturedResponse(status_code=200 if passed else 500, headers={}, body=b"ok" if passed else b"err")
    replay_res = ReplayResult(original=original, replayed=replayed)
    return RetryResult(attempts=1, final_result=replay_res, all_results=[replay_res])


@pytest.fixture
def runner():
    return CliRunner()


def test_missing_request_shows_error(runner, tmp_path):
    result = runner.invoke(retry_group, ["run", "no-such-id", "--store", str(tmp_path)])
    assert result.exit_code == 1
    assert "not found" in result.output


@patch("req_replay.cli_retry.retry_replay")
@patch("req_replay.cli_retry.RequestStore")
def test_run_retry_passes(mock_store_cls, mock_retry, runner, tmp_path):
    store = MagicMock()
    store.load.return_value = _make_request()
    mock_store_cls.return_value = store
    mock_retry.return_value = _make_retry_result(passed=True)

    result = runner.invoke(retry_group, ["run", "req-1", "--store", str(tmp_path)])
    assert result.exit_code == 0
    assert "PASS" in result.output


@patch("req_replay.cli_retry.retry_replay")
@patch("req_replay.cli_retry.RequestStore")
def test_run_retry_fails_exits_1(mock_store_cls, mock_retry, runner, tmp_path):
    store = MagicMock()
    store.load.return_value = _make_request()
    mock_store_cls.return_value = store
    mock_retry.return_value = _make_retry_result(passed=False)

    result = runner.invoke(retry_group, ["run", "req-1", "--store", str(tmp_path)])
    assert result.exit_code == 1
    assert "FAIL" in result.output


@patch("req_replay.cli_retry.retry_replay")
@patch("req_replay.cli_retry.RequestStore")
def test_run_retry_passes_config(mock_store_cls, mock_retry, runner, tmp_path):
    store = MagicMock()
    store.load.return_value = _make_request()
    mock_store_cls.return_value = store
    mock_retry.return_value = _make_retry_result(passed=True)

    runner.invoke(
        retry_group,
        ["run", "req-1", "--store", str(tmp_path),
         "--max-attempts", "5", "--backoff", "0.5", "--multiplier", "1.5"],
    )
    _, kwargs = mock_retry.call_args
    config = kwargs.get("config") or mock_retry.call_args.args[1]
    assert config.max_attempts == 5
    assert config.backoff_seconds == pytest.approx(0.5)
    assert config.backoff_multiplier == pytest.approx(1.5)
