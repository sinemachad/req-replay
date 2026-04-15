"""Unit tests for req_replay.schedule."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from req_replay.diff import DiffResult
from req_replay.replay import ReplayResult
from req_replay.schedule import ScheduleConfig, ScheduleEvent, schedule_replay


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_diff(*, status_mismatch: bool = False, body_mismatch: bool = False) -> DiffResult:
    return DiffResult(
        status_mismatch=status_mismatch,
        body_mismatch=body_mismatch,
        header_diffs={},
        expected_status=200,
        actual_status=200 if not status_mismatch else 500,
        expected_body=b"ok",
        actual_body=b"ok" if not body_mismatch else b"fail",
    )


def _make_result(*, passed: bool = True) -> ReplayResult:
    diff = _make_diff(status_mismatch=not passed)
    return MagicMock(spec=ReplayResult, passed=passed, diff=diff)


def _make_request() -> MagicMock:
    return MagicMock()


# ---------------------------------------------------------------------------
# ScheduleEvent
# ---------------------------------------------------------------------------

def test_schedule_event_passed():
    result = _make_result(passed=True)
    event = ScheduleEvent(iteration=1, timestamp=datetime.utcnow(), result=result)
    assert event.passed is True


def test_schedule_event_failed():
    result = _make_result(passed=False)
    event = ScheduleEvent(iteration=2, timestamp=datetime.utcnow(), result=result)
    assert event.passed is False


def test_schedule_event_summary_contains_iteration():
    result = _make_result(passed=True)
    event = ScheduleEvent(iteration=3, timestamp=datetime.utcnow(), result=result)
    assert "iteration=3" in event.summary


def test_schedule_event_summary_contains_pass():
    result = _make_result(passed=True)
    event = ScheduleEvent(iteration=1, timestamp=datetime.utcnow(), result=result)
    assert "PASS" in event.summary


# ---------------------------------------------------------------------------
# schedule_replay
# ---------------------------------------------------------------------------

@patch("req_replay.schedule.replay_request")
def test_schedule_respects_max_iterations(mock_replay):
    mock_replay.return_value = _make_result(passed=True)
    config = ScheduleConfig(interval_seconds=0, max_iterations=3)
    events = list(schedule_replay(_make_request(), config, _sleep=lambda _: None))
    assert len(events) == 3
    assert mock_replay.call_count == 3


@patch("req_replay.schedule.replay_request")
def test_schedule_stops_on_failure(mock_replay):
    mock_replay.return_value = _make_result(passed=False)
    config = ScheduleConfig(interval_seconds=0, max_iterations=10, stop_on_failure=True)
    events = list(schedule_replay(_make_request(), config, _sleep=lambda _: None))
    assert len(events) == 1


@patch("req_replay.schedule.replay_request")
def test_schedule_calls_on_event_callback(mock_replay):
    mock_replay.return_value = _make_result(passed=True)
    config = ScheduleConfig(interval_seconds=0, max_iterations=2)
    received: list = []
    list(schedule_replay(_make_request(), config, on_event=received.append, _sleep=lambda _: None))
    assert len(received) == 2


@patch("req_replay.schedule.replay_request")
def test_schedule_sleeps_between_iterations(mock_replay):
    mock_replay.return_value = _make_result(passed=True)
    config = ScheduleConfig(interval_seconds=5.0, max_iterations=2)
    sleep_calls: list[float] = []
    list(schedule_replay(_make_request(), config, _sleep=sleep_calls.append))
    # sleep is called between iterations, so once for 2 iterations
    assert sleep_calls == [5.0]
