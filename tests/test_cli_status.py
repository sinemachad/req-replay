"""Tests for req_replay.cli_status."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest
from click.testing import CliRunner

from req_replay.cli_status import status_group
from req_replay.models import CapturedRequest
from req_replay.storage import RequestStore


@pytest.fixture()
def runner():
    return CliRunner()


def _make_request(store_path: str, code: int, method: str = "GET") -> None:
    store = RequestStore(store_path)
    req = CapturedRequest(
        id=f"r-{code}-{method}",
        method=method,
        url="http://example.com/api",
        headers={},
        body="",
        timestamp=datetime(2024, 1, 1),
        metadata={"response": {"status_code": code, "headers": {}, "body": "", "elapsed_ms": 5.0}},
    )
    store.save(req)


def test_analyze_empty_store(runner, tmp_path):
    result = runner.invoke(status_group, ["analyze", "--store", str(tmp_path)])
    assert result.exit_code == 0
    assert "No responses" in result.output


def test_analyze_shows_codes(runner, tmp_path):
    _make_request(str(tmp_path), 200)
    _make_request(str(tmp_path), 404)
    result = runner.invoke(status_group, ["analyze", "--store", str(tmp_path)])
    assert result.exit_code == 0
    assert "200" in result.output
    assert "404" in result.output


def test_analyze_filter_by_method(runner, tmp_path):
    _make_request(str(tmp_path), 200, "GET")
    _make_request(str(tmp_path), 500, "POST")
    result = runner.invoke(status_group, ["analyze", "--store", str(tmp_path), "--method", "GET"])
    assert result.exit_code == 0
    assert "200" in result.output
    assert "500" not in result.output


def test_codes_lists_unique(runner, tmp_path):
    _make_request(str(tmp_path), 200)
    _make_request(str(tmp_path), 200)
    _make_request(str(tmp_path), 201)
    result = runner.invoke(status_group, ["codes", "--store", str(tmp_path)])
    assert result.exit_code == 0
    assert result.output.count("200") == 1
    assert "201" in result.output


def test_codes_empty_store(runner, tmp_path):
    result = runner.invoke(status_group, ["codes", "--store", str(tmp_path)])
    assert result.exit_code == 0
    assert "No responses" in result.output
