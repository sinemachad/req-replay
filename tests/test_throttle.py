"""Tests for req_replay.throttle."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.replay import ReplayResult
from req_replay.throttle import ThrottleConfig, ThrottleEvent, ThrottleResult, throttle_replay


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_request(req_id: str = "req-1") -> CapturedRequest:
    return CapturedRequest(
        id=req_id,
        method="GET",
        url="https://example.com/api",
        headers={},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
    )


def _make_result(passed: bool = True) -> ReplayResult:
    diff = MagicMock()
    diff.is_identical = passed
    return ReplayResult(
        original=_make_request(),
        replayed=MagicMock(),
        diff=diff,
    )


def _make_store(requests):
    store = MagicMock()
    store.load.side_effect = lambda rid: next(r for r in requests if r.id == rid)
    store.list_ids.return_value = [r.id for r in requests]
    return store


# ---------------------------------------------------------------------------
# ThrottleEvent
# ---------------------------------------------------------------------------

def test_throttle_event_passed():
    event = ThrottleEvent(iteration=1, request_id="r1", result=_make_result(True), elapsed=0.1)
    assert event.passed is True


def test_throttle_event_failed():
    event = ThrottleEvent(iteration=1, request_id="r1", result=_make_result(False), elapsed=0.2)
    assert event.passed is False


def test_throttle_event_summary_contains_iteration():
    event = ThrottleEvent(iteration=3, request_id="r3", result=_make_result(True), elapsed=0.05)
    assert "iteration=3" in event.summary
    assert "PASS" in event.summary


# ---------------------------------------------------------------------------
# ThrottleResult
# ---------------------------------------------------------------------------

def test_throttle_result_all_pass():
    events = [ThrottleEvent(i, f"r{i}", _make_result(True), 0.1) for i in range(1, 4)]
    tr = ThrottleResult(events=events)
    assert tr.passed is True
    assert "PASS" in tr.summary


def test_throttle_result_one_fail():
    events = [
        ThrottleEvent(1, "r1", _make_result(True), 0.1),
        ThrottleEvent(2, "r2", _make_result(False), 0.1),
    ]
    tr = ThrottleResult(events=events)
    assert tr.passed is False
    assert "1 failed" in tr.summary


# ---------------------------------------------------------------------------
# throttle_replay
# ---------------------------------------------------------------------------

def test_throttle_replay_replays_all_ids():
    reqs = [_make_request(f"req-{i}") for i in range(3)]
    store = _make_store(reqs)
    ids = [r.id for r in reqs]
    sleep_calls = []
    result = throttle_replay(
        ids, store,
        ThrottleConfig(delay_seconds=0.5, burst=1),
        _replay_fn=lambda r, b: _make_result(True),
        _sleep_fn=lambda s: sleep_calls.append(s),
    )
    assert len(result.events) == 3


def test_throttle_replay_respects_max_requests():
    reqs = [_make_request(f"req-{i}") for i in range(5)]
    store = _make_store(reqs)
    ids = [r.id for r in reqs]
    result = throttle_replay(
        ids, store,
        ThrottleConfig(max_requests=2),
        _replay_fn=lambda r, b: _make_result(True),
        _sleep_fn=lambda s: None,
    )
    assert len(result.events) == 2


def test_throttle_replay_sleeps_between_bursts():
    reqs = [_make_request(f"req-{i}") for i in range(4)]
    store = _make_store(reqs)
    ids = [r.id for r in reqs]
    sleep_calls: list = []
    throttle_replay(
        ids, store,
        ThrottleConfig(delay_seconds=1.0, burst=2),
        _replay_fn=lambda r, b: _make_result(True),
        _sleep_fn=lambda s: sleep_calls.append(s),
    )
    # burst=2 over 4 requests → sleep after index 2 only (not after last)
    assert sleep_calls == [1.0]


def test_throttle_replay_no_sleep_after_last():
    reqs = [_make_request("only")]
    store = _make_store(reqs)
    sleep_calls: list = []
    throttle_replay(
        ["only"], store,
        ThrottleConfig(delay_seconds=5.0, burst=1),
        _replay_fn=lambda r, b: _make_result(True),
        _sleep_fn=lambda s: sleep_calls.append(s),
    )
    assert sleep_calls == []
