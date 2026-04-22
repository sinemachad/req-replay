"""Tests for req_replay.header_coerce."""
from __future__ import annotations

import pytest

from req_replay.header_coerce import (
    CoerceChange,
    CoerceResult,
    coerce_headers,
    coerce_request_headers,
)
from req_replay.models import CapturedRequest


def _req(headers: dict) -> CapturedRequest:
    return CapturedRequest(
        id="test-id",
        method="POST",
        url="https://example.com/api",
        headers=headers,
        body=None,
        timestamp="2024-01-01T00:00:00Z",
        tags=[],
        metadata={},
    )


# ---------------------------------------------------------------------------
# coerce_headers
# ---------------------------------------------------------------------------

def test_no_coercible_headers_returns_unchanged():
    result = coerce_headers({"X-Custom": "SomeValue"})
    assert result.headers == {"X-Custom": "SomeValue"}
    assert not result.changed


def test_content_type_value_lowercased():
    result = coerce_headers({"content-type": "Application/JSON"})
    assert result.headers["content-type"] == "application/json"
    assert result.changed


def test_accept_value_lowercased():
    result = coerce_headers({"Accept": "Text/HTML"})
    assert result.headers["Accept"] == "text/html"


def test_leading_trailing_whitespace_stripped():
    result = coerce_headers({"content-type": "  application/json  "})
    assert result.headers["content-type"] == "application/json"
    assert result.changed


def test_already_canonical_value_no_change():
    result = coerce_headers({"content-type": "application/json"})
    assert not result.changed


def test_non_coercible_header_whitespace_stripped():
    result = coerce_headers({"X-Request-Id": "  abc123  "})
    assert result.headers["X-Request-Id"] == "abc123"
    assert result.changed


def test_multiple_headers_mixed():
    headers = {
        "content-type": "APPLICATION/JSON",
        "X-Trace": "trace-id",
        "accept-encoding": "GZIP, DEFLATE",
    }
    result = coerce_headers(headers)
    assert result.headers["content-type"] == "application/json"
    assert result.headers["X-Trace"] == "trace-id"
    assert result.headers["accept-encoding"] == "gzip, deflate"


def test_changes_list_populated_correctly():
    result = coerce_headers({"content-type": "TEXT/PLAIN"})
    assert len(result.changes) == 1
    change = result.changes[0]
    assert change.header == "content-type"
    assert change.original == "TEXT/PLAIN"
    assert change.coerced == "text/plain"


def test_change_to_dict():
    c = CoerceChange(header="content-type", original="TEXT/PLAIN", coerced="text/plain")
    d = c.to_dict()
    assert d == {"header": "content-type", "original": "TEXT/PLAIN", "coerced": "text/plain"}


def test_display_no_changes():
    result = CoerceResult(headers={}, changes=[])
    assert result.display() == "No coercions applied."


def test_display_with_changes():
    result = coerce_headers({"content-type": "TEXT/HTML"})
    display = result.display()
    assert "content-type" in display
    assert "TEXT/HTML" in display
    assert "text/html" in display


# ---------------------------------------------------------------------------
# coerce_request_headers
# ---------------------------------------------------------------------------

def test_coerce_request_headers_returns_new_request():
    req = _req({"content-type": "APPLICATION/JSON"})
    updated, result = coerce_request_headers(req)
    assert updated is not req
    assert updated.headers["content-type"] == "application/json"


def test_coerce_request_headers_preserves_other_fields():
    req = _req({"content-type": "text/plain"})
    updated, _ = coerce_request_headers(req)
    assert updated.id == req.id
    assert updated.method == req.method
    assert updated.url == req.url


def test_coerce_request_headers_does_not_mutate_original():
    headers = {"content-type": "TEXT/XML"}
    req = _req(headers)
    coerce_request_headers(req)
    assert req.headers["content-type"] == "TEXT/XML"
