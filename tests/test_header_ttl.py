"""Tests for req_replay.header_ttl."""
from __future__ import annotations

from req_replay.header_ttl import (
    TTLResult,
    TTLStats,
    analyze_ttl,
    extract_ttl,
)
from req_replay.models import CapturedRequest, CapturedResponse


def _req(url: str = "https://example.com/") -> CapturedRequest:
    return CapturedRequest(
        id="r1",
        method="GET",
        url=url,
        headers={},
        body=None,
        metadata={},
        tags=[],
    )


def _resp(headers: dict) -> CapturedResponse:
    return CapturedResponse(status_code=200, headers=headers, body=None)


# ---------------------------------------------------------------------------
# extract_ttl
# ---------------------------------------------------------------------------

def test_no_cache_headers_returns_none():
    ttl, source = extract_ttl(_resp({}))
    assert ttl is None
    assert source is None


def test_max_age_extracted_from_cache_control():
    ttl, source = extract_ttl(_resp({"cache-control": "public, max-age=3600"}))
    assert ttl == 3600
    assert source == "cache-control"


def test_max_age_case_insensitive_header_key():
    ttl, source = extract_ttl(_resp({"Cache-Control": "max-age=300"}))
    assert ttl == 300
    assert source == "cache-control"


def test_cdn_cache_control_used_when_no_cache_control():
    ttl, source = extract_ttl(_resp({"cdn-cache-control": "max-age=120"}))
    assert ttl == 120
    assert source == "cdn-cache-control"


def test_cache_control_takes_priority_over_cdn():
    ttl, source = extract_ttl(
        _resp({"cache-control": "max-age=60", "cdn-cache-control": "max-age=120"})
    )
    assert ttl == 60
    assert source == "cache-control"


def test_no_max_age_directive_returns_none():
    ttl, source = extract_ttl(_resp({"cache-control": "no-store, no-cache"}))
    assert ttl is None


def test_malformed_max_age_returns_none():
    ttl, source = extract_ttl(_resp({"cache-control": "max-age=abc"}))
    assert ttl is None


# ---------------------------------------------------------------------------
# analyze_ttl
# ---------------------------------------------------------------------------

def test_empty_pairs_returns_zero_stats():
    stats = analyze_ttl([])
    assert stats.total == 0
    assert stats.with_ttl == 0
    assert stats.without_ttl == 0
    assert stats.average_ttl is None


def test_analyze_single_pair_with_ttl():
    pairs = [(_req(), _resp({"cache-control": "max-age=600"}))]
    stats = analyze_ttl(pairs)
    assert stats.total == 1
    assert stats.with_ttl == 1
    assert stats.without_ttl == 0
    assert stats.average_ttl == 600.0


def test_analyze_mixed_pairs():
    pairs = [
        (_req("https://a.com/"), _resp({"cache-control": "max-age=200"})),
        (_req("https://b.com/"), _resp({})),
    ]
    stats = analyze_ttl(pairs)
    assert stats.total == 2
    assert stats.with_ttl == 1
    assert stats.without_ttl == 1
    assert stats.average_ttl == 200.0


def test_average_ttl_across_multiple():
    pairs = [
        (_req(), _resp({"cache-control": "max-age=100"})),
        (_req(), _resp({"cache-control": "max-age=300"})),
    ]
    stats = analyze_ttl(pairs)
    assert stats.average_ttl == 200.0


# ---------------------------------------------------------------------------
# TTLResult display
# ---------------------------------------------------------------------------

def test_result_display_with_ttl():
    r = TTLResult(request_id="abc", url="https://x.com/", ttl_seconds=42, source="cache-control")
    text = r.display()
    assert "42s" in text
    assert "cache-control" in text


def test_result_display_without_ttl():
    r = TTLResult(request_id="abc", url="https://x.com/", ttl_seconds=None, source=None)
    assert "none" in r.display()


# ---------------------------------------------------------------------------
# TTLStats display
# ---------------------------------------------------------------------------

def test_stats_display_contains_totals():
    pairs = [(_req(), _resp({"cache-control": "max-age=60"}))]
    stats = analyze_ttl(pairs)
    text = stats.display()
    assert "1" in text
    assert "60" in text
