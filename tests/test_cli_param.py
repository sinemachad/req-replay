"""Tests for req_replay.cli_param."""
import json
import pytest
from click.testing import CliRunner
from pathlib import Path
from req_replay.cli_param import param_group
from req_replay.models import CapturedRequest
from req_replay.storage import RequestStore


def _make_request(rid="abc123", url="https://example.com/?q=test", body=None, headers=None):
    return CapturedRequest(
        id=rid,
        url=url,
        method="GET",
        headers=headers or {},
        body=body,
        timestamp="2024-01-01T00:00:00",
        tags=[],
    )


@pytest.fixture
def runner():
    return CliRunner()


def test_show_missing_request_shows_error(runner, tmp_path):
    result = runner.invoke(param_group, ["show", "no-such-id", "--store", str(tmp_path)])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_show_displays_query_params(runner, tmp_path):
    store = RequestStore(tmp_path)
    req = _make_request(url="https://example.com/?foo=bar")
    store.save(req)
    result = runner.invoke(param_group, ["show", req.id, "--store", str(tmp_path)])
    assert result.exit_code == 0
    assert "foo" in result.output
    assert "bar" in result.output


def test_show_displays_body_params(runner, tmp_path):
    store = RequestStore(tmp_path)
    req = _make_request(
        url="https://example.com/api",
        headers={"Content-Type": "application/json"},
        body=json.dumps({"user": "alice"}),
    )
    store.save(req)
    result = runner.invoke(param_group, ["show", req.id, "--store", str(tmp_path)])
    assert result.exit_code == 0
    assert "user" in result.output


def test_list_empty_store(runner, tmp_path):
    result = runner.invoke(param_group, ["list", "--store", str(tmp_path)])
    assert result.exit_code == 0
    assert "No requests found" in result.output


def test_list_has_query_filter(runner, tmp_path):
    store = RequestStore(tmp_path)
    r1 = _make_request(rid="r1", url="https://example.com/?x=1")
    r2 = _make_request(rid="r2", url="https://example.com/plain")
    store.save(r1)
    store.save(r2)
    result = runner.invoke(param_group, ["list", "--has-query", "--store", str(tmp_path)])
    assert result.exit_code == 0
    assert "r1" in result.output
    assert "r2" not in result.output
