"""Tests for req_replay.pipeline."""
from unittest.mock import patch, MagicMock
import pytest

from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.assert_rules import AssertionRule
from req_replay.transform import TransformConfig
from req_replay.pipeline import PipelineStep, PipelineResult, StepResult, run_pipeline
from req_replay.replay import ReplayResult
from req_replay.diff import DiffResult


def _req():
    return CapturedRequest(
        id="r1",
        method="GET",
        url="https://example.com/api",
        headers={},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


def _resp(status=200):
    return CapturedResponse(status_code=status, headers={}, body=None)


def _make_replay_result(status=200):
    actual = _resp(status)
    diff = DiffResult(status_match=True, body_match=True, header_diffs={})
    return ReplayResult(request=_req(), expected=actual, actual=actual, diff=diff)


def test_step_result_passed_when_all_assertions_pass():
    from req_replay.assert_rules import AssertionResult
    sr = StepResult(
        step_name="s1",
        assertion_results=[AssertionResult(rule="status == 200", passed=True, detail="")],
    )
    assert sr.passed is True


def test_step_result_failed_when_assertion_fails():
    from req_replay.assert_rules import AssertionResult
    sr = StepResult(
        step_name="s1",
        assertion_results=[AssertionResult(rule="status == 201", passed=False, detail="got 200")],
    )
    assert sr.passed is False


def test_step_result_failed_when_error_set():
    sr = StepResult(step_name="s1", error="connection refused")
    assert sr.passed is False
    assert "error" in sr.summary()


def test_pipeline_result_passed_all_steps_pass():
    sr = StepResult(step_name="s1")
    pr = PipelineResult(step_results=[sr])
    assert pr.passed is True


def test_pipeline_summary_contains_overall_status():
    sr = StepResult(step_name="s1")
    pr = PipelineResult(step_results=[sr])
    assert "Pipeline" in pr.summary()
    assert "PASS" in pr.summary()


@patch("req_replay.pipeline.replay_request")
def test_run_pipeline_no_steps_returns_empty(mock_replay):
    result = run_pipeline(_req(), [])
    assert result.step_results == []
    mock_replay.assert_not_called()


@patch("req_replay.pipeline.replay_request")
def test_run_pipeline_calls_replay_for_each_step(mock_replay):
    mock_replay.return_value = _make_replay_result()
    steps = [PipelineStep(name="step1"), PipelineStep(name="step2")]
    result = run_pipeline(_req(), steps)
    assert len(result.step_results) == 2
    assert mock_replay.call_count == 2


@patch("req_replay.pipeline.replay_request")
def test_run_pipeline_captures_exception_as_error(mock_replay):
    mock_replay.side_effect = RuntimeError("network error")
    steps = [PipelineStep(name="boom")]
    result = run_pipeline(_req(), steps)
    assert result.step_results[0].error == "network error"
    assert not result.passed


@patch("req_replay.pipeline.replay_request")
def test_run_pipeline_applies_transform(mock_replay):
    mock_replay.return_value = _make_replay_result()
    tc = TransformConfig(base_url="https://staging.example.com")
    steps = [PipelineStep(name="transformed", transform=tc)]
    run_pipeline(_req(), steps)
    called_req = mock_replay.call_args[0][0]
    assert "staging" in called_req.url
