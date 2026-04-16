"""Tests for req_replay.cli_mock."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from req_replay.cli_mock import mock_group
from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.storage import RequestStore


@pytest.fixture()
def runner():
    return CliRunner()


def _make_request(store_path: Path, method: str = "GET", url: str = "http://example.com/api") -> str:
    store = RequestStore(store_path)
    req = CapturedRequest(method=method, url=url, headers={}, body=None, tags=[])
    store.save(req)
    return req.id


def _make_snapshot(store_path: Path, req_id: str, status: int = 200) -> None:
    snap_dir = store_path / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    resp = CapturedResponse(status_code=status, headers={}, body="ok", elapsed_ms=5.0)
    (snap_dir / f"{req_id}.json").write_text(json.dumps(resp.to_dict()))


def test_build_creates_rules_file(tmp_path, runner):
    store_path = tmp_path / "store"
    req_id = _make_request(store_path)
    _make_snapshot(store_path, req_id)
    output = tmp_path / "rules.json"
    result = runner.invoke(mock_group, ["build", str(store_path), str(output)])
    assert result.exit_code == 0
    assert output.exists()
    rules = json.loads(output.read_text())
    assert len(rules) == 1
    assert rules[0]["method"] == "GET"


def test_build_no_requests(tmp_path, runner):
    store_path = tmp_path / "empty"
    store_path.mkdir()
    output = tmp_path / "rules.json"
    result = runner.invoke(mock_group, ["build", str(store_path), str(output)])
    assert "No requests" in result.output


def test_list_rules(tmp_path, runner):
    rules = [
        {"method": "GET", "path": "/api", "match_query": False,
         "response": {"status_code": 200, "headers": {}, "body": "ok", "elapsed_ms": 1.0}}
    ]
    rules_file = tmp_path / "rules.json"
    rules_file.write_text(json.dumps(rules))
    result = runner.invoke(mock_group, ["list", str(rules_file)])
    assert result.exit_code == 0
    assert "GET" in result.output
    assert "/api" in result.output


def test_list_empty_rules(tmp_path, runner):
    rules_file = tmp_path / "rules.json"
    rules_file.write_text("[]")
    result = runner.invoke(mock_group, ["list", str(rules_file)])
    assert "No rules" in result.output
