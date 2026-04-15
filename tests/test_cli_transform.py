"""Tests for the transform CLI commands."""

from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from req_replay.cli_transform import transform_group
from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.replay import ReplayResult


def _make_request(url="https://api.example.com/data"):
    return CapturedRequest(
        id="abc123",
        timestamp=datetime.now(timezone.utc),
        method="GET",
        url=url,
        headers={"Accept": "application/json"},
        body=None,
        tags=[],
    )


def _make_response(status=200, body="{}"):
    return CapturedResponse(
        status_code=status,
        headers={"Content-Type": "application/json"},
        body=body,
        elapsed_ms=50.0,
    )


@pytest.fixture
def runner():
    return CliRunner()


def test_replay_transformed_missing_request(runner, tmp_path):
    result = runner.invoke(
        transform_group,
        ["replay", "nonexistent", "--store-dir", str(tmp_path)],
    )
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_replay_transformed_calls_replay(runner, tmp_path):
    req = _make_request()
    resp = _make_response()
    replay_result = ReplayResult(
        request=req,
        original_response=resp,
        replayed_response=resp,
    )

    with patch("req_replay.cli_transform.RequestStore") as MockStore, \
         patch("req_replay.cli_transform.replay_request", return_value=replay_result):
        mock_store = MagicMock()
        mock_store.load.return_value = req
        MockStore.return_value = mock_store

        result = runner.invoke(
            transform_group,
            ["replay", "abc123", "--store-dir", str(tmp_path),
             "--base-url", "https://staging.example.com"],
        )

    assert result.exit_code == 0
    assert "staging.example.com" in result.output


def test_replay_transformed_invalid_header_format(runner, tmp_path):
    req = _make_request()

    with patch("req_replay.cli_transform.RequestStore") as MockStore:
        mock_store = MagicMock()
        mock_store.load.return_value = req
        MockStore.return_value = mock_store

        result = runner.invoke(
            transform_group,
            ["replay", "abc123", "--store-dir", str(tmp_path),
             "--set-header", "BADVALUE"],
        )

    assert result.exit_code != 0
    assert "KEY:VALUE" in result.output


def test_replay_transformed_exits_1_on_failure(runner, tmp_path):
    req = _make_request()
    original = _make_response(status=200, body='{"ok": true}')
    replayed = _make_response(status=500, body='{"error": "oops"}')
    replay_result = ReplayResult(
        request=req,
        original_response=original,
        replayed_response=replayed,
    )

    with patch("req_replay.cli_transform.RequestStore") as MockStore, \
         patch("req_replay.cli_transform.replay_request", return_value=replay_result):
        mock_store = MagicMock()
        mock_store.load.return_value = req
        MockStore.return_value = mock_store

        result = runner.invoke(
            transform_group,
            ["replay", "abc123", "--store-dir", str(tmp_path)],
        )

    assert result.exit_code == 1
