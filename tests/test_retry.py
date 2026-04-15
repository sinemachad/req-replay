"""Tests for req_replay.retry."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.replay import ReplayResult
from req_replay.retry import RetryConfig, RetryResult, retry_replay


def _make_request() -> CapturedRequest:
    return CapturedRequest(
        id="req-1",
        method="GET",
        url="http://example.com/api",
        headers={},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
    )


def _make_result(passed: bool, status: int = 200) -> ReplayResult:
    original = CapturedResponse(status_code=200, headers={}, body=b"ok")
    replayed = CapturedResponse(status_code=status, headers={}, body=b"ok" if passed else b"fail")
    return ReplayResult(original=original, replayed=replayed)


@patch("req_replay.retry.time.sleep")
@patch("req_replay.retry.replay_request")
def test_retry_succeeds_on_first_attempt(mock_replay, mock_sleep):
    mock_replay.return_value = _make_result(passed=True)
    req = _make_request()
    result = retry_replay(req, RetryConfig(max_attempts=3))
    assert result.passed
    assert result.attempts == 1
    mock_sleep.assert_not_called()


@patch("req_replay.retry.time.sleep")
@patch("req_replay.retry.replay_request")
def test_retry_retries_on_diff_failure(mock_replay, mock_sleep):
    fail = _make_result(passed=False)
    ok = _make_result(passed=True)
    mock_replay.side_effect = [fail, ok]
    req = _make_request()
    result = retry_replay(req, RetryConfig(max_attempts=3, backoff_seconds=0.1))
    assert result.passed
    assert result.attempts == 2
    mock_sleep.assert_called_once()


@patch("req_replay.retry.time.sleep")
@patch("req_replay.retry.replay_request")
def test_retry_exhausts_all_attempts(mock_replay, mock_sleep):
    mock_replay.return_value = _make_result(passed=False)
    req = _make_request()
    result = retry_replay(req, RetryConfig(max_attempts=3, backoff_seconds=0.0))
    assert not result.passed
    assert result.attempts == 3
    assert len(result.all_results) == 3


@patch("req_replay.retry.time.sleep")
@patch("req_replay.retry.replay_request")
def test_no_retry_on_diff_when_disabled(mock_replay, mock_sleep):
    mock_replay.return_value = _make_result(passed=False)
    req = _make_request()
    config = RetryConfig(max_attempts=3, retry_on_diff=False, retry_on_status=[])
    result = retry_replay(req, config)
    assert result.attempts == 1
    mock_sleep.assert_not_called()


@patch("req_replay.retry.time.sleep")
@patch("req_replay.retry.replay_request")
def test_backoff_multiplier_applied(mock_replay, mock_sleep):
    mock_replay.return_value = _make_result(passed=False)
    req = _make_request()
    config = RetryConfig(max_attempts=3, backoff_seconds=1.0, backoff_multiplier=3.0)
    retry_replay(req, config)
    calls = [c.args[0] for c in mock_sleep.call_args_list]
    assert calls[0] == pytest.approx(1.0)
    assert calls[1] == pytest.approx(3.0)


def test_retry_result_summary_pass():
    r = _make_result(passed=True)
    rr = RetryResult(attempts=2, final_result=r, all_results=[r, r])
    assert "PASS" in rr.summary
    assert "2 attempt" in rr.summary


def test_retry_result_summary_fail():
    r = _make_result(passed=False)
    rr = RetryResult(attempts=3, final_result=r, all_results=[r, r, r])
    assert "FAIL" in rr.summary
