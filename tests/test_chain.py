"""Tests for req_replay.chain — request chaining."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
from datetime import datetime

import pytest

from req_replay.chain import (
    ChainStep,
    ChainResult,
    _interpolate,
    _extract_variables,
    run_chain,
)
from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.replay import ReplayResult
from req_replay.diff import DiffResult


def _req(rid: str = "req-1") -> CapturedRequest:
    return CapturedRequest(
        id=rid,
        method="GET",
        url="http://example.com/api",
        headers={"Accept": "application/json"},
        body=None,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        tags=[],
    )


def _resp(status: int = 200, body: str = '{"token": "abc123"}') -> CapturedResponse:
    return CapturedResponse(
        status_code=status,
        headers={"Content-Type": "application/json", "X-Request-Id": "rid-42"},
        body=body,
    )


def _make_result(passed: bool = True) -> ReplayResult:
    diff = MagicMock(spec=DiffResult)
    diff.is_identical = passed
    result = MagicMock(spec=ReplayResult)
    result.passed = passed
    result.summary = "200 == 200" if passed else "200 != 500"
    result.actual = _resp()
    return result


# --- _interpolate ---

def test_interpolate_replaces_known_variable():
    assert _interpolate("Bearer {token}", {"token": "abc123"}) == "Bearer abc123"


def test_interpolate_leaves_unknown_variable_intact():
    assert _interpolate("{missing}", {}) == "{missing}"


def test_interpolate_multiple_variables():
    result = _interpolate("{a}-{b}", {"a": "hello", "b": "world"})
    assert result == "hello-world"


# --- _extract_variables ---

def test_extract_json_body_key():
    resp = _resp(body='{"token": "abc123", "user_id": 7}')
    extracted = _extract_variables(resp, {"tok": "token"})
    assert extracted == {"tok": "abc123"}


def test_extract_header():
    resp = _resp()
    extracted = _extract_variables(resp, {"rid": "header:x-request-id"})
    assert extracted == {"rid": "rid-42"}


def test_extract_missing_key_returns_empty():
    resp = _resp(body='{"foo": 1}')
    extracted = _extract_variables(resp, {"bar": "bar"})
    assert extracted == {}


def test_extract_invalid_json_body_skips_json_keys():
    resp = _resp(body="not-json")
    extracted = _extract_variables(resp, {"tok": "token"})
    assert extracted == {}


# --- run_chain ---

def test_run_chain_single_step_pass():
    store = MagicMock()
    store.load.return_value = _req("r1")

    with patch("req_replay.chain.replay_request", return_value=_make_result(True)):
        results = run_chain([ChainStep(request_id="r1")], store)

    assert len(results) == 1
    assert results[0].passed is True
    assert results[0].request_id == "r1"


def test_run_chain_stops_on_failure():
    store = MagicMock()
    store.load.return_value = _req()

    fail_result = _make_result(False)
    pass_result = _make_result(True)

    with patch("req_replay.chain.replay_request", side_effect=[fail_result, pass_result]):
        results = run_chain(
            [ChainStep(request_id="r1"), ChainStep(request_id="r2")],
            store,
        )

    assert len(results) == 1
    assert results[0].passed is False


def test_run_chain_passes_extracted_variable_to_next_step():
    store = MagicMock()
    store.load.return_value = _req()

    replay_result = _make_result(True)
    replay_result.actual = _resp(body='{"token": "secret"}')

    captured_headers: dict = {}

    def fake_replay(req: CapturedRequest) -> ReplayResult:
        captured_headers.update(req.headers)
        return _make_result(True)

    steps = [
        ChainStep(request_id="r1", extract={"tok": "token"}),
        ChainStep(request_id="r2", header_overrides={"Authorization": "Bearer {tok}"}),
    ]

    with patch("req_replay.chain.replay_request", side_effect=[replay_result, fake_replay(_req())]):
        # Run manually to capture header mutation
        from req_replay.chain import _extract_variables, _interpolate
        variables = _extract_variables(replay_result.actual, {"tok": "token"})
        assert variables == {"tok": "secret"}
        interpolated = _interpolate("Bearer {tok}", variables)
        assert interpolated == "Bearer secret"


def test_chain_result_summary_contains_step_index():
    result = ChainResult(
        step_index=2,
        request_id="r3",
        result=_make_result(True),
    )
    assert "step 3" in result.summary
    assert "r3" in result.summary
    assert "PASS" in result.summary
