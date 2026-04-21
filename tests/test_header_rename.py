"""Tests for req_replay.header_rename."""
from __future__ import annotations

import pytest

from req_replay.header_rename import rename_headers, rename_request_headers, RenameResult
from req_replay.models import CapturedRequest


def _req(headers: dict) -> CapturedRequest:
    return CapturedRequest(
        id="test-id",
        method="GET",
        url="https://example.com/api",
        headers=headers,
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


# ---------------------------------------------------------------------------
# rename_headers
# ---------------------------------------------------------------------------

def test_empty_headers_returns_empty():
    result = rename_headers({}, {"X-Old": "X-New"})
    assert result.renamed_headers == {}
    assert not result.changed


def test_no_rename_map_returns_original():
    headers = {"content-type": "application/json"}
    result = rename_headers(headers, {})
    assert result.renamed_headers == headers
    assert not result.changed


def test_simple_rename_applied():
    headers = {"X-Old-Header": "value"}
    result = rename_headers(headers, {"X-Old-Header": "X-New-Header"})
    assert "X-New-Header" in result.renamed_headers
    assert "X-Old-Header" not in result.renamed_headers
    assert result.renamed_headers["X-New-Header"] == "value"
    assert result.changed


def test_rename_is_case_insensitive_on_existing_key():
    headers = {"x-old-header": "value"}
    result = rename_headers(headers, {"X-Old-Header": "X-New-Header"})
    assert "X-New-Header" in result.renamed_headers
    assert result.changed


def test_rename_preserves_value():
    headers = {"Authorization": "Bearer secret"}
    result = rename_headers(headers, {"Authorization": "X-Auth-Token"})
    assert result.renamed_headers["X-Auth-Token"] == "Bearer secret"


def test_unrelated_headers_preserved():
    headers = {"content-type": "application/json", "x-old": "val"}
    result = rename_headers(headers, {"x-old": "x-new"})
    assert "content-type" in result.renamed_headers
    assert result.renamed_headers["content-type"] == "application/json"


def test_same_name_rename_not_applied():
    """If old and new names are the same (case-insensitively), no rename occurs."""
    headers = {"x-header": "value"}
    result = rename_headers(headers, {"x-header": "x-header"})
    assert not result.changed
    assert result.renamed_headers == {"x-header": "value"}


def test_multiple_renames_applied():
    headers = {"x-a": "1", "x-b": "2", "x-c": "3"}
    result = rename_headers(headers, {"x-a": "x-alpha", "x-b": "x-beta"})
    assert "x-alpha" in result.renamed_headers
    assert "x-beta" in result.renamed_headers
    assert "x-c" in result.renamed_headers
    assert len(result.renames_applied) == 2


def test_display_no_changes():
    result = rename_headers({}, {})
    assert result.display() == "No headers renamed."


def test_display_with_changes():
    headers = {"x-old": "v"}
    result = rename_headers(headers, {"x-old": "x-new"})
    display = result.display()
    assert "x-old" in display
    assert "x-new" in display


# ---------------------------------------------------------------------------
# rename_request_headers
# ---------------------------------------------------------------------------

def test_rename_request_headers_returns_updated_request():
    req = _req({"x-request-id": "abc", "content-type": "text/plain"})
    updated, result = rename_request_headers(req, {"x-request-id": "x-correlation-id"})
    assert "x-correlation-id" in updated.headers
    assert updated.headers["x-correlation-id"] == "abc"
    assert result.changed


def test_rename_request_headers_does_not_mutate_original():
    req = _req({"x-old": "value"})
    rename_request_headers(req, {"x-old": "x-new"})
    assert "x-old" in req.headers


def test_rename_request_headers_preserves_other_fields():
    req = _req({"x-old": "v"})
    updated, _ = rename_request_headers(req, {"x-old": "x-new"})
    assert updated.id == req.id
    assert updated.method == req.method
    assert updated.url == req.url
    assert updated.timestamp == req.timestamp
