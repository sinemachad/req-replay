"""Tests for req_replay.header_inject."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from req_replay.models import CapturedRequest
from req_replay.header_inject import inject_headers, InjectionResult
from req_replay.cli_header_inject import header_inject_group


def _req(headers: dict | None = None) -> CapturedRequest:
    return CapturedRequest(
        id="abc123",
        method="GET",
        url="https://example.com/api",
        headers=headers or {},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


# --- unit tests ---

def test_inject_adds_new_header():
    req = _req({"accept": "application/json"})
    new_req, result = inject_headers(req, {"x-custom": "yes"})
    assert new_req.headers["x-custom"] == "yes"
    assert "x-custom" in result.added
    assert result.changed is True


def test_inject_overwrites_existing_header_by_default():
    req = _req({"authorization": "Bearer old"})
    new_req, result = inject_headers(req, {"authorization": "Bearer new"})
    assert new_req.headers["authorization"] == "Bearer new"
    assert "authorization" in result.overridden
    assert result.added == []


def test_inject_no_overwrite_leaves_existing_header():
    req = _req({"authorization": "Bearer old"})
    new_req, result = inject_headers(req, {"authorization": "Bearer new"}, overwrite=False)
    assert new_req.headers["authorization"] == "Bearer old"
    assert result.overridden == []
    assert result.added == []
    assert result.changed is False


def test_inject_normalises_header_keys_to_lowercase():
    req = _req({})
    new_req, result = inject_headers(req, {"X-Trace-ID": "abc"})
    assert "x-trace-id" in new_req.headers
    assert "x-trace-id" in result.added


def test_inject_does_not_mutate_original():
    req = _req({"accept": "*/*"})
    inject_headers(req, {"accept": "application/json"})
    assert req.headers["accept"] == "*/*"


def test_no_headers_injected_returns_unchanged_result():
    req = _req({"accept": "*/*"})
    new_req, result = inject_headers(req, {})
    assert result.changed is False
    assert new_req.headers == {"accept": "*/*"}


def test_display_shows_added_and_overridden():
    req = _req({"accept": "*/*"})
    _, result = inject_headers(req, {"accept": "application/json", "x-new": "1"})
    text = result.display()
    assert "overridden" in text.lower() or "added" in text.lower()


# --- CLI tests ---

@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_apply_missing_request_shows_error(runner, tmp_path):
    result = runner.invoke(
        header_inject_group,
        ["apply", "missing-id", "x-foo=bar", "--store", str(tmp_path)],
    )
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "not found" in (result.stderr or "").lower()


def test_cli_apply_injects_and_prints(runner, tmp_path):
    from req_replay.storage import RequestStore
    store = RequestStore(str(tmp_path))
    req = _req({"accept": "*/*"})
    store.save(req)

    result = runner.invoke(
        header_inject_group,
        ["apply", "abc123", "x-injected=hello", "--store", str(tmp_path)],
    )
    assert result.exit_code == 0
    assert "x-injected" in result.output


def test_cli_apply_save_persists_headers(runner, tmp_path):
    from req_replay.storage import RequestStore
    store = RequestStore(str(tmp_path))
    req = _req({"accept": "*/*"})
    store.save(req)

    runner.invoke(
        header_inject_group,
        ["apply", "abc123", "x-saved=yes", "--store", str(tmp_path), "--save"],
    )
    loaded = store.load("abc123")
    assert loaded.headers.get("x-saved") == "yes"
