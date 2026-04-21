"""Tests for req_replay.header_normalize."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from req_replay.header_normalize import (
    NormalizeResult,
    normalize_headers,
    normalize_request_headers,
)


def _req(headers=None):
    r = MagicMock()
    r.headers = headers or {}
    r.id = "test-id"
    return r


# ---------------------------------------------------------------------------
# normalize_headers
# ---------------------------------------------------------------------------

def test_empty_headers_returns_empty():
    result = normalize_headers({})
    assert result.normalized == {}
    assert not result.changed


def test_lowercase_keys():
    result = normalize_headers({"Content-Type": "application/json"})
    assert "content-type" in result.normalized
    assert "Content-Type" not in result.normalized
    assert result.changed


def test_strip_values():
    result = normalize_headers({"accept": "  text/html  "})
    assert result.normalized["accept"] == "text/html"
    assert result.changed


def test_remove_empty_header():
    result = normalize_headers({"x-empty": ""})
    assert "x-empty" not in result.normalized
    assert result.changed


def test_keep_empty_header_when_disabled():
    result = normalize_headers({"x-empty": ""}, remove_empty=False)
    assert "x-empty" in result.normalized


def test_no_change_when_already_normalized():
    result = normalize_headers({"content-type": "application/json"})
    assert not result.changed
    assert result.normalized == {"content-type": "application/json"}


def test_canonical_only_drops_unknown():
    result = normalize_headers(
        {"content-type": "application/json", "x-custom": "foo"},
        canonical_only=True,
    )
    assert "content-type" in result.normalized
    assert "x-custom" not in result.normalized
    assert result.changed


def test_canonical_only_keeps_known():
    result = normalize_headers(
        {"host": "example.com", "authorization": "Bearer tok"},
        canonical_only=True,
    )
    assert "host" in result.normalized
    assert "authorization" in result.normalized


def test_multiple_changes_recorded():
    result = normalize_headers({
        "Content-Type": "  application/json  ",
        "X-Empty": "",
    })
    assert len(result.changes) >= 2


# ---------------------------------------------------------------------------
# NormalizeResult.display
# ---------------------------------------------------------------------------

def test_display_no_changes():
    r = NormalizeResult(original={}, normalized={}, changes=[])
    assert "already normalized" in r.display()


def test_display_with_changes():
    r = NormalizeResult(
        original={"Content-Type": "text/plain"},
        normalized={"content-type": "text/plain"},
        changes=["renamed 'Content-Type' -> 'content-type'"],
    )
    assert "1 header" in r.display()
    assert "Content-Type" in r.display()


# ---------------------------------------------------------------------------
# normalize_request_headers
# ---------------------------------------------------------------------------

def test_normalize_request_headers_returns_new_object():
    from req_replay.models import CapturedRequest
    from datetime import datetime
    req = CapturedRequest(
        id="abc",
        method="GET",
        url="https://example.com",
        headers={"Content-Type": "application/json"},
        body=None,
        timestamp=datetime.utcnow(),
        tags=[],
        metadata={},
    )
    new_req = normalize_request_headers(req)
    assert new_req is not req
    assert "content-type" in new_req.headers
    assert req.headers == {"Content-Type": "application/json"}  # not mutated
