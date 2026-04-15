"""Tests for the schedule CLI group."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from req_replay.cli_schedule import schedule_group
from req_replay.diff import DiffResult
from req_replay.replay import ReplayResult
from req_replay.schedule import ScheduleEvent


@pytest.fixture()
def runner():
    return CliRunner()


def _make_diff(**kwargs) -> DiffResult:
    defaults = dict(
        status_mismatch=False,
        body_mismatch=False,
        header_diffs={},
        expected_status=200,
        actual_status=200,
        expected_body=b"ok",
        actual_body=b"ok",
    )
    defaults.update(kwargs)
    return DiffResult(**defaults)


def _make_event(*, passed: bool = True, iteration: int = 1) -> ScheduleEvent:
    diff = _make_diff(status_mismatch=not passed, actual_status=200 if passed else 500)
    result = MagicMock(spec=ReplayResult, passed=passed, diff=diff)
    return ScheduleEvent(iteration=iteration, timestamp=datetime.utcnow(), result=result)


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_missing_request_shows_error(runner, tmp_path):
    result = runner.invoke(
        schedule_group,
        ["run", "nonexistent-id", "--store-path", str(tmp_path), "--max-iterations", "1"],
    )
    assert result.exit_code != 0
    assert "not found" in result.output


@patch("req_replay.cli_schedule.schedule_replay")
@patch("req_replay.cli_schedule.RequestStore")
def test_run_schedule_calls_schedule_replay(mock_store_cls, mock_schedule, runner, tmp_path):
    mock_store = MagicMock()
    mock_store.load.return_value = MagicMock()
    mock_store_cls.return_value = mock_store
    mock_schedule.return_value = iter([_make_event(passed=True)])

    result = runner.invoke(
        schedule_group,
        ["run", "abc123", "--store-path", str(tmp_path), "--max-iterations", "1"],
    )
    assert result.exit_code == 0
    mock_schedule.assert_called_once()


@patch("req_replay.cli_schedule.schedule_replay")
@patch("req_replay.cli_schedule.RequestStore")
def test_run_schedule_prints_pass(mock_store_cls, mock_schedule, runner, tmp_path):
    mock_store = MagicMock()
    mock_store.load.return_value = MagicMock()
    mock_store_cls.return_value = mock_store
    mock_schedule.return_value = iter([_make_event(passed=True, iteration=1)])

    result = runner.invoke(
        schedule_group,
        ["run", "abc123", "--store-path", str(tmp_path)],
    )
    assert "PASS" in result.output


@patch("req_replay.cli_schedule.schedule_replay")
@patch("req_replay.cli_schedule.RequestStore")
def test_run_schedule_verbose_shows_status_on_failure(
    mock_store_cls, mock_schedule, runner, tmp_path
):
    mock_store = MagicMock()
    mock_store.load.return_value = MagicMock()
    mock_store_cls.return_value = mock_store
    mock_schedule.return_value = iter([_make_event(passed=False, iteration=1)])

    result = runner.invoke(
        schedule_group,
        ["run", "abc123", "--store-path", str(tmp_path), "--verbose"],
    )
    assert "status" in result.output
