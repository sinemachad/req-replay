"""Tests for req_replay.idempotency."""
import pytest
from req_replay.idempotency import analyze_idempotency, IdempotencyResult
from req_replay.models import CapturedRequest
from datetime import datetime, timezone


def _req(method: str, url: str, body: str | None = None) -> CapturedRequest:
    return CapturedRequest(
        id="test-id",
        method=method,
        url=url,
        headers={},
        body=body,
        timestamp=datetime.now(timezone.utc).isoformat(),
        tags=[],
        metadata={},
    )


def test_empty_list_returns_clean():
    result = analyze_idempotency([])
    assert result.passed
    assert result.summary.startswith("OK")


def test_single_get_is_clean():
    result = analyze_idempotency([_req("GET", "https://example.com/items")])
    assert result.passed


def test_single_post_with_body_is_clean():
    result = analyze_idempotency([_req("POST", "https://example.com/items", body='{"x":1}')])
    assert result.passed


def test_post_without_body_raises_i002():
    result = analyze_idempotency([_req("POST", "https://example.com/items")])
    codes = [w.code for w in result.warnings]
    assert "I002" in codes
    assert not result.passed


def test_repeated_post_raises_i001():
    reqs = [
        _req("POST", "https://example.com/orders", body='{"a":1}'),
        _req("POST", "https://example.com/orders", body='{"a":2}'),
    ]
    result = analyze_idempotency(reqs)
    codes = [w.code for w in result.warnings]
    assert "I001" in codes


def test_repeated_post_different_urls_no_i001():
    reqs = [
        _req("POST", "https://example.com/a", body='{"x":1}'),
        _req("POST", "https://example.com/b", body='{"x":1}'),
    ]
    result = analyze_idempotency(reqs)
    codes = [w.code for w in result.warnings]
    assert "I001" not in codes


def test_summary_contains_count_when_warnings():
    reqs = [_req("POST", "https://example.com/x")]
    result = analyze_idempotency(reqs)
    assert "1" in result.summary


def test_display_contains_code():
    reqs = [_req("POST", "https://example.com/x")]
    result = analyze_idempotency(reqs)
    assert "I002" in result.display()


def test_to_dict_structure():
    reqs = [_req("POST", "https://example.com/x")]
    result = analyze_idempotency(reqs)
    d = result.warnings[0].to_dict()
    assert set(d.keys()) == {"code", "method", "url", "message"}
