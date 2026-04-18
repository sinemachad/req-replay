"""Tests for req_replay.cache."""
from req_replay.cache import analyze_cache, summarize_cache, CacheInfo
from req_replay.models import CapturedRequest, CapturedResponse


def _resp(headers: dict, status: int = 200) -> CapturedResponse:
    return CapturedResponse(status_code=status, headers=headers, body=None)


def _req() -> CapturedRequest:
    return CapturedRequest(
        method="GET",
        url="https://example.com/",
        headers={},
        body=None,
    )


# --- analyze_cache ---

def test_no_cache_headers_not_cacheable():
    info = analyze_cache(_resp({}))
    assert info.is_cacheable is False
    assert info.cache_control is None


def test_no_store_not_cacheable():
    info = analyze_cache(_resp({"Cache-Control": "no-store"}))
    assert info.is_cacheable is False
    assert "no-store" in info.directives


def test_private_not_cacheable():
    info = analyze_cache(_resp({"Cache-Control": "private, max-age=600"}))
    assert info.is_cacheable is False


def test_public_max_age_is_cacheable():
    info = analyze_cache(_resp({"Cache-Control": "public, max-age=3600"}))
    assert info.is_cacheable is True


def test_etag_extracted():
    info = analyze_cache(_resp({"ETag": '"abc123"', "Cache-Control": "public, max-age=60"}))
    assert info.etag == '"abc123"'


def test_last_modified_extracted():
    info = analyze_cache(_resp({"Last-Modified": "Wed, 21 Oct 2015 07:28:00 GMT",
                                 "Cache-Control": "public, max-age=60"}))
    assert info.last_modified == "Wed, 21 Oct 2015 07:28:00 GMT"


def test_age_parsed_as_int():
    info = analyze_cache(_resp({"Cache-Control": "public, max-age=3600", "Age": "120"}))
    assert info.age == 120


def test_age_missing_is_none():
    info = analyze_cache(_resp({"Cache-Control": "public, max-age=3600"}))
    assert info.age is None


def test_vary_extracted():
    info = analyze_cache(_resp({"Cache-Control": "public, max-age=60", "Vary": "Accept-Encoding"}))
    assert info.vary == "Accept-Encoding"


def test_expires_makes_cacheable_without_max_age():
    info = analyze_cache(_resp({"Cache-Control": "public", "Expires": "Thu, 01 Jan 2099 00:00:00 GMT"}))
    assert info.is_cacheable is True
    assert info.expires == "Thu, 01 Jan 2099 00:00:00 GMT"


def test_display_contains_cacheable_label():
    info = analyze_cache(_resp({"Cache-Control": "public, max-age=3600"}))
    out = info.display()
    assert "Cacheable" in out
    assert "True" in out


# --- summarize_cache ---

def test_summarize_empty():
    result = summarize_cache([])
    assert result["total"] == 0
    assert result["cacheable_pct"] == 0.0


def test_summarize_counts():
    pairs = [
        (_req(), _resp({"Cache-Control": "public, max-age=60"})),
        (_req(), _resp({"Cache-Control": "no-store"})),
        (_req(), _resp({})),
    ]
    result = summarize_cache(pairs)
    assert result["total"] == 3
    assert result["cacheable"] == 1
    assert result["uncacheable"] == 2
    assert result["cacheable_pct"] == round(1 / 3 * 100, 1)
