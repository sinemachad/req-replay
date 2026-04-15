"""Tests for req_replay.watch."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.replay import ReplayResult
from req_replay.watch import WatchConfig, WatchEvent, watch_request


def _make_request() -> CapturedRequest:
    return CapturedRequest(
        id="abc",
        timestamp=datetime.utcnow().isoformat(),
        method="GET",
        url="http://example.com/",
        headers={},
        body=None,
        tags=[],
    )


def _make_result(passed: bool) -> ReplayResult:
    resp = CapturedResponse(status_code=200 if passed else 500, headers={}, body=b"ok")
    original = CapturedResponse(status_code=200, headers={}, body=b"ok")
    return ReplayResult(original=original, replayed=resp)


# ---------------------------------------------------------------------------
# WatchEvent
# ---------------------------------------------------------------------------

def test_watch_event_passed():
    event = WatchEvent(timestamp=datetime.utcnow(), result=_make_result(True), iteration=1)
    assert event.passed is True


def test_watch_event_failed():
    event = WatchEvent(timestamp=datetime.utcnow(), result=_make_result(False), iteration=1)
    assert event.passed is False


def test_watch_event_summary_contains_iteration():
    event = WatchEvent(timestamp=datetime.utcnow(), result=_make_result(True), iteration=7)
    assert "#7" in event.summary()


def test_watch_event_summary_pass_label():
    event = WatchEvent(timestamp=datetime.utcnow(), result=_make_result(True), iteration=1)
    assert "PASS" in event.summary()


def test_watch_event_summary_fail_label():
    event = WatchEvent(timestamp=datetime.utcnow(), result=_make_result(False), iteration=1)
    assert "FAIL" in event.summary()


# ---------------------------------------------------------------------------
# watch_request
# ---------------------------------------------------------------------------

@patch("req_replay.watch.time.sleep")
@patch("req_replay.watch.replay_request")
def test_max_iterations(mock_replay, mock_sleep):
    mock_replay.return_value = _make_result(True)
    config = WatchConfig(interval_seconds=0, max_iterations=3)
    events = watch_request(_make_request(), config)
    assert len(events) == 3
    assert mock_replay.call_count == 3


@patch("req_replay.watch.time.sleep")
@patch("req_replay.watch.replay_request")
def test_stop_on_failure(mock_replay, mock_sleep):
    results = [_make_result(True), _make_result(False), _make_result(True)]
    mock_replay.side_effect = results
    config = WatchConfig(interval_seconds=0, stop_on_failure=True, max_iterations=10)
    events = watch_request(_make_request(), config)
    # Should stop after the second (failing) event
    assert len(events) == 2
    assert events[-1].passed is False


@patch("req_replay.watch.time.sleep")
@patch("req_replay.watch.replay_request")
def test_on_event_callback_called(mock_replay, mock_sleep):
    mock_replay.return_value = _make_result(True)
    config = WatchConfig(interval_seconds=0, max_iterations=4)
    received = []
    watch_request(_make_request(), config, on_event=received.append)
    assert len(received) == 4


@patch("req_replay.watch.time.sleep")
@patch("req_replay.watch.replay_request")
def test_sleep_called_between_iterations(mock_replay, mock_sleep):
    mock_replay.return_value = _make_result(True)
    config = WatchConfig(interval_seconds=2.5, max_iterations=3)
    watch_request(_make_request(), config)
    # sleep is called after each iteration except the last
    assert mock_sleep.call_count == 2
    mock_sleep.assert_called_with(2.5)
