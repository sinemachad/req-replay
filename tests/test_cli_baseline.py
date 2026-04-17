"""Tests for req_replay.cli_baseline."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from req_replay.cli_baseline import baseline_group
from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.baseline import save_baseline
from req_replay.replay import ReplayResult
from req_replay.diff import DiffResult


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


def _make_response(status: int = 200) -> CapturedResponse:
    return CapturedResponse(
        status_code=status,
        headers={"content-type": "application/json"},
        body='{"ok": true}',
    )


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_list_empty(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(baseline_group, ["list", "--store", str(tmp_path)])
    assert result.exit_code == 0
    assert "No baselines" in result.output


def test_list_shows_ids(runner: CliRunner, tmp_path: Path) -> None:
    save_baseline(tmp_path, "req-1", _make_response())
    result = runner.invoke(baseline_group, ["list", "--store", str(tmp_path)])
    assert "req-1" in result.output


def test_delete_missing(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(baseline_group, ["delete", "req-1", "--store", str(tmp_path)])
    assert result.exit_code == 0
    assert "No baseline" in result.output


def test_delete_existing(runner: CliRunner, tmp_path: Path) -> None:
    save_baseline(tmp_path, "req-1", _make_response())
    result = runner.invoke(baseline_group, ["delete", "req-1", "--store", str(tmp_path)])
    assert "deleted" in result.output


def test_save_missing_request(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(baseline_group, ["save", "no-such", "--store", str(tmp_path)])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_check_missing_request(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(baseline_group, ["check", "no-such", "--store", str(tmp_path)])
    assert result.exit_code == 1
    assert "not found" in result.output
