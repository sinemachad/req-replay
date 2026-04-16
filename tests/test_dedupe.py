"""Tests for req_replay.dedupe."""
import pytest
from datetime import datetime, timezone

from req_replay.models import CapturedRequest
from req_replay.dedupe import _request_fingerprint, deduplicate


def _req(
    method: str = "GET",
    url: str = "https://example.com/api",
    headers: dict | None = None,
    body: str | None = None,
) -> CapturedRequest:
    return CapturedRequest(
        id="test-id",
        method=method,
        url=url,
        headers=headers or {},
        body=body,
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        tags=[],
    )


def test_fingerprint_same_request_is_stable():
    r = _req()
    assert _request_fingerprint(r) == _request_fingerprint(r)


def test_fingerprint_different_method_differs():
    assert _request_fingerprint(_req(method="GET")) != _request_fingerprint(_req(method="POST"))


def test_fingerprint_different_url_differs():
    assert _request_fingerprint(_req(url="https://a.com")) != _request_fingerprint(_req(url="https://b.com"))


def test_fingerprint_header_keys_case_insensitive():
    r1 = _req(headers={"Content-Type": "application/json"})
    r2 = _req(headers={"content-type": "application/json"})
    assert _request_fingerprint(r1) == _request_fingerprint(r2)


def test_no_duplicates_returns_all():
    requests = [_req(url=f"https://example.com/{i}") for i in range(3)]
    result = deduplicate(requests)
    assert len(result.unique) == 3
    assert result.duplicate_count == 0


def test_exact_duplicates_removed():
    r = _req()
    result = deduplicate([r, r, r])
    assert len(result.unique) == 1
    assert result.duplicate_count == 2


def test_first_occurrence_is_kept():
    r1 = _req(url="https://example.com/a")
    r2 = _req(url="https://example.com/a")
    result = deduplicate([r1, r2])
    assert result.unique[0] is r1
    assert result.duplicates[0] == (r1, r2)


def test_mixed_requests_partial_dedup():
    r_a = _req(url="https://example.com/a")
    r_b = _req(url="https://example.com/b")
    r_a2 = _req(url="https://example.com/a")
    result = deduplicate([r_a, r_b, r_a2])
    assert len(result.unique) == 2
    assert result.duplicate_count == 1


def test_summary_string():
    r = _req()
    result = deduplicate([r, r])
    assert "1 unique" in result.summary()
    assert "1 duplicate" in result.summary()


def test_empty_list():
    result = deduplicate([])
    assert result.unique == []
    assert result.duplicate_count == 0
