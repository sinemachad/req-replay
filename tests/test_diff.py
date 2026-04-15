"""Tests for req_replay.diff module."""

import pytest

from req_replay.diff import DiffResult, diff_responses
from req_replay.models import CapturedResponse


def _resp(
    status: int = 200,
    body: str = '{"ok": true}',
    headers: dict | None = None,
) -> CapturedResponse:
    return CapturedResponse(
        status_code=status,
        headers=headers or {"content-type": "application/json"},
        body=body,
    )


def test_identical_responses_are_identical():
    r = diff_responses(_resp(), _resp())
    assert r.is_identical
    assert r.status_match
    assert r.body_match
    assert r.header_diffs == {}


def test_status_mismatch_detected():
    r = diff_responses(_resp(status=200), _resp(status=404))
    assert not r.status_match
    assert not r.is_identical
    assert r.original_status == 200
    assert r.replayed_status == 404


def test_body_mismatch_detected():
    r = diff_responses(_resp(body='{"a": 1}'), _resp(body='{"a": 2}'))
    assert not r.body_match
    assert not r.is_identical


def test_json_semantic_equality():
    """Bodies that are semantically equal JSON should not count as a mismatch."""
    r = diff_responses(
        _resp(body='{"b": 2, "a": 1}'),
        _resp(body='{"a": 1, "b": 2}'),
    )
    assert r.body_match


def test_header_diff_detected():
    r = diff_responses(
        _resp(headers={"content-type": "application/json"}),
        _resp(headers={"content-type": "text/plain"}),
    )
    assert "content-type" in r.header_diffs
    assert r.header_diffs["content-type"] == ("application/json", "text/plain")
    assert not r.is_identical


def test_ignored_headers_not_in_diff():
    r = diff_responses(
        _resp(headers={"content-type": "application/json", "date": "Mon, 1 Jan 2024"}),
        _resp(headers={"content-type": "application/json", "date": "Tue, 2 Jan 2024"}),
    )
    assert "date" not in r.header_diffs
    assert r.is_identical


def test_custom_ignore_headers():
    r = diff_responses(
        _resp(headers={"x-custom": "aaa"}),
        _resp(headers={"x-custom": "bbb"}),
        ignore_headers=["x-custom"],
    )
    assert "x-custom" not in r.header_diffs


def test_summary_identical():
    r = diff_responses(_resp(), _resp())
    assert r.summary() == "Responses are identical."


def test_summary_shows_differences():
    r = diff_responses(_resp(status=200), _resp(status=500))
    summary = r.summary()
    assert "STATUS" in summary
    assert "200" in summary
    assert "500" in summary
