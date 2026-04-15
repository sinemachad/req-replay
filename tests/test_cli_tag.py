"""Tests for req_replay.cli_tag."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from req_replay.cli_tag import tag_group
from req_replay.models import CapturedRequest


def _make_request(id: str = "req-1", tags: list[str] | None = None) -> CapturedRequest:
    return CapturedRequest(
        id=id,
        timestamp="2024-01-01T00:00:00",
        method="GET",
        url="https://example.com",
        headers={},
        body=None,
        tags=tags or [],
    )


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_add_missing_request_shows_error(runner: CliRunner) -> None:
    with patch("req_replay.cli_tag.RequestStore") as MockStore:
        MockStore.return_value.load.side_effect = FileNotFoundError
        result = runner.invoke(tag_group, ["add", "missing-id", "smoke"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_add_saves_updated_request(runner: CliRunner) -> None:
    req = _make_request(tags=["existing"])
    with patch("req_replay.cli_tag.RequestStore") as MockStore:
        instance = MockStore.return_value
        instance.load.return_value = req
        result = runner.invoke(tag_group, ["add", "req-1", "smoke", "ci"])
    assert result.exit_code == 0
    instance.save.assert_called_once()
    saved: CapturedRequest = instance.save.call_args[0][0]
    assert "smoke" in saved.tags
    assert "ci" in saved.tags
    assert "existing" in saved.tags


def test_remove_missing_request_shows_error(runner: CliRunner) -> None:
    with patch("req_replay.cli_tag.RequestStore") as MockStore:
        MockStore.return_value.load.side_effect = FileNotFoundError
        result = runner.invoke(tag_group, ["remove", "missing-id", "smoke"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_remove_saves_updated_request(runner: CliRunner) -> None:
    req = _make_request(tags=["smoke", "ci"])
    with patch("req_replay.cli_tag.RequestStore") as MockStore:
        instance = MockStore.return_value
        instance.load.return_value = req
        result = runner.invoke(tag_group, ["remove", "req-1", "smoke"])
    assert result.exit_code == 0
    saved: CapturedRequest = instance.save.call_args[0][0]
    assert "smoke" not in saved.tags
    assert "ci" in saved.tags


def test_summary_no_tags_shows_message(runner: CliRunner) -> None:
    with patch("req_replay.cli_tag.RequestStore") as MockStore:
        MockStore.return_value.list.return_value = [_make_request(tags=[])]
        result = runner.invoke(tag_group, ["summary"])
    assert result.exit_code == 0
    assert "No tags" in result.output


def test_summary_displays_tag_counts(runner: CliRunner) -> None:
    requests = [
        _make_request(id="1", tags=["smoke"]),
        _make_request(id="2", tags=["smoke", "ci"]),
    ]
    with patch("req_replay.cli_tag.RequestStore") as MockStore:
        MockStore.return_value.list.return_value = requests
        result = runner.invoke(tag_group, ["summary"])
    assert result.exit_code == 0
    assert "smoke" in result.output
    assert "ci" in result.output
