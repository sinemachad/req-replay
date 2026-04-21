"""Tests for req_replay.header_strip."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from click.testing import CliRunner

from req_replay.header_strip import (
    DEFAULT_STRIP_HEADERS,
    StripResult,
    strip_headers,
    strip_request_headers,
)
from req_replay.models import CapturedRequest
from req_replay.cli_header_strip import header_strip_group
from req_replay.storage import RequestStore


def _req(
    headers: dict | None = None,
    rid: str = "abc123",
) -> CapturedRequest:
    return CapturedRequest(
        id=rid,
        method="POST",
        url="https://example.com/api",
        headers=headers or {"Content-Type": "application/json", "Host": "example.com"},
        body='{"x": 1}',
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        tags=[],
        metadata={},
    )


# ---------------------------------------------------------------------------
# strip_headers
# ---------------------------------------------------------------------------

def test_default_strip_removes_host():
    result = strip_headers({"Host": "example.com", "Accept": "*/*"})
    assert "Host" not in result.stripped_headers
    assert "Accept" in result.stripped_headers


def test_default_strip_removes_content_length():
    result = strip_headers({"Content-Length": "42", "Authorization": "Bearer tok"})
    assert "Content-Length" not in result.stripped_headers
    assert "Authorization" in result.stripped_headers


def test_strip_case_insensitive():
    result = strip_headers({"CONTENT-LENGTH": "10", "X-Custom": "val"})
    assert "CONTENT-LENGTH" not in result.stripped_headers
    assert "X-Custom" in result.stripped_headers


def test_no_defaults_keeps_host():
    result = strip_headers({"Host": "example.com"}, use_defaults=False)
    assert "Host" in result.stripped_headers
    assert result.removed == []


def test_extra_strip_removes_custom_header():
    result = strip_headers(
        {"X-Debug": "1", "Accept": "*/*"},
        strip=["X-Debug"],
        use_defaults=False,
    )
    assert "X-Debug" not in result.stripped_headers
    assert "Accept" in result.stripped_headers


def test_changed_is_false_when_nothing_removed():
    result = strip_headers({"Authorization": "Bearer tok"}, use_defaults=False)
    assert not result.changed


def test_changed_is_true_when_header_removed():
    result = strip_headers({"Host": "example.com"})
    assert result.changed


def test_display_no_changes():
    result = strip_headers({"Authorization": "Bearer tok"}, use_defaults=False)
    assert "No headers stripped" in result.display()


def test_display_lists_removed_headers():
    result = strip_headers({"Host": "example.com", "Connection": "keep-alive"})
    text = result.display()
    assert "Host" in text or "host" in text.lower()


# ---------------------------------------------------------------------------
# strip_request_headers
# ---------------------------------------------------------------------------

def test_strip_request_returns_new_object():
    req = _req()
    new_req, _ = strip_request_headers(req)
    assert new_req is not req


def test_strip_request_preserves_id_and_method():
    req = _req()
    new_req, _ = strip_request_headers(req)
    assert new_req.id == req.id
    assert new_req.method == req.method


def test_strip_request_removes_host_by_default():
    req = _req(headers={"Host": "example.com", "Content-Type": "application/json"})
    new_req, result = strip_request_headers(req)
    assert "Host" not in new_req.headers
    assert result.changed


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


def test_check_missing_request_shows_error(runner, tmp_path):
    result = runner.invoke(
        header_strip_group,
        ["check", "nonexistent", "--store", str(tmp_path)],
    )
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "not found" in (result.stderr or "")


def test_check_outputs_strip_result(runner, tmp_path):
    store = RequestStore(tmp_path)
    req = _req(headers={"Host": "example.com", "Accept": "*/*"})
    store.save(req)
    result = runner.invoke(
        header_strip_group,
        ["check", req.id, "--store", str(tmp_path)],
    )
    assert result.exit_code == 0


def test_apply_saves_updated_request(runner, tmp_path):
    store = RequestStore(tmp_path)
    req = _req(headers={"Host": "example.com", "Authorization": "Bearer tok"})
    store.save(req)
    result = runner.invoke(
        header_strip_group,
        ["apply", req.id, "--store", str(tmp_path)],
    )
    assert result.exit_code == 0
    updated = store.load(req.id)
    assert all(k.lower() != "host" for k in updated.headers)
