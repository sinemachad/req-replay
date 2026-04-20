"""Tests for req_replay.cli_header_audit."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from req_replay.cli_header_audit import header_audit_group
from req_replay.models import CapturedRequest
from req_replay.storage import RequestStore


@pytest.fixture()
def runner():
    return CliRunner()


def _make_request(
    req_id: str = "req-1",
    headers: dict | None = None,
) -> CapturedRequest:
    return CapturedRequest(
        id=req_id,
        method="GET",
        url="https://example.com/api",
        headers=headers or {"content-type": "application/json", "accept": "*/*", "user-agent": "test"},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


def test_check_missing_request_shows_error(runner, tmp_path):
    result = runner.invoke(
        header_audit_group,
        ["check", "nonexistent", "--store", str(tmp_path)],
    )
    assert result.exit_code == 1
    assert "not found" in result.output


def test_check_clean_request_shows_ok(runner, tmp_path):
    store = RequestStore(str(tmp_path))
    req = _make_request()
    store.save(req)
    result = runner.invoke(
        header_audit_group,
        ["check", req.id, "--store", str(tmp_path)],
    )
    assert result.exit_code == 0
    assert "OK" in result.output


def test_check_warns_on_sensitive_header(runner, tmp_path):
    store = RequestStore(str(tmp_path))
    req = _make_request(
        headers={"Authorization": "Bearer secret", "content-type": "application/json", "accept": "*/*", "user-agent": "test"}
    )
    store.save(req)
    result = runner.invoke(
        header_audit_group,
        ["check", req.id, "--store", str(tmp_path)],
    )
    assert result.exit_code == 0
    assert "HA001" in result.output


def test_scan_no_requests(runner, tmp_path):
    result = runner.invoke(
        header_audit_group,
        ["scan", "--store", str(tmp_path)],
    )
    assert result.exit_code == 0
    assert "No requests" in result.output


def test_scan_shows_results(runner, tmp_path):
    store = RequestStore(str(tmp_path))
    for i in range(2):
        store.save(_make_request(req_id=f"req-{i}"))
    result = runner.invoke(
        header_audit_group,
        ["scan", "--store", str(tmp_path)],
    )
    assert result.exit_code == 0
    assert "req-0" in result.output
    assert "req-1" in result.output


def test_scan_only_failures_hides_clean(runner, tmp_path):
    store = RequestStore(str(tmp_path))
    clean = _make_request(req_id="clean-req")
    store.save(clean)
    result = runner.invoke(
        header_audit_group,
        ["scan", "--store", str(tmp_path), "--only-failures"],
    )
    assert result.exit_code == 0
    assert "clean-req" not in result.output
