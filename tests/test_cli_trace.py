"""Tests for req_replay.cli_trace."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from req_replay.cli_trace import trace_group
from req_replay.models import CapturedRequest
from req_replay.storage import RequestStore


def _make_request(request_id: str = "req-1", metadata: dict | None = None) -> CapturedRequest:
    return CapturedRequest(
        id=request_id,
        method="GET",
        url="https://example.com/api",
        headers={},
        body=None,
        timestamp="2024-01-01T00:00:00+00:00",
        tags=[],
        metadata=metadata or {},
    )


@pytest.fixture()
def runner():
    return CliRunner()


def test_show_missing_request_shows_error(runner, tmp_path):
    result = runner.invoke(trace_group, ["show", "missing-id", "--store", str(tmp_path)])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_show_no_spans_shows_message(runner, tmp_path):
    store = RequestStore(tmp_path)
    req = _make_request()
    store.save(req)
    result = runner.invoke(trace_group, ["show", "req-1", "--store", str(tmp_path)])
    assert result.exit_code == 0
    assert "No trace spans" in result.output


def test_show_displays_spans(runner, tmp_path):
    spans = [
        {
            "name": "dns",
            "started_at": "2024-01-01T00:00:00+00:00",
            "ended_at": "2024-01-01T00:00:00+00:00",
            "duration_ms": 5.0,
            "metadata": {},
        }
    ]
    store = RequestStore(tmp_path)
    req = _make_request(metadata={"trace_spans": spans})
    store.save(req)
    result = runner.invoke(trace_group, ["show", "req-1", "--store", str(tmp_path)])
    assert result.exit_code == 0
    assert "dns" in result.output


def test_add_missing_request_shows_error(runner, tmp_path):
    result = runner.invoke(
        trace_group, ["add", "missing", "dns", "5.0", "--store", str(tmp_path)]
    )
    assert result.exit_code != 0
    assert "not found" in result.output


def test_add_span_persists(runner, tmp_path):
    store = RequestStore(tmp_path)
    req = _make_request()
    store.save(req)
    result = runner.invoke(
        trace_group,
        ["add", "req-1", "connect", "12.5", "--meta", "host=example.com", "--store", str(tmp_path)],
    )
    assert result.exit_code == 0
    assert "connect" in result.output

    saved = store.load("req-1")
    spans = saved.metadata.get("trace_spans", [])
    assert len(spans) == 1
    assert spans[0]["name"] == "connect"
    assert spans[0]["duration_ms"] == 12.5
    assert spans[0]["metadata"] == {"host": "example.com"}
