"""Tests for req_replay.redirect."""
import pytest
from req_replay.redirect import RedirectHop, RedirectChain, analyze_redirects, REDIRECT_CODES
from req_replay.models import CapturedRequest, CapturedResponse
from datetime import datetime


def _req(url: str = "https://example.com/") -> CapturedRequest:
    return CapturedRequest(
        id="abc", method="GET", url=url, headers={}, body=None, timestamp=datetime.utcnow()
    )


def _resp(status: int, location: str | None = None) -> CapturedResponse:
    headers = {"location": location} if location else {}
    return CapturedResponse(status_code=status, headers=headers, body=None, elapsed_ms=10)


def test_empty_pairs_returns_empty_chain():
    chain = analyze_redirects([])
    assert chain.length == 0
    assert chain.final_url is None


def test_non_redirect_response_not_added():
    pairs = [(_req(), _resp(200))]
    chain = analyze_redirects(pairs)
    assert chain.length == 0


def test_single_redirect_hop():
    pairs = [(_req("https://a.com/"), _resp(301, "https://b.com/"))]
    chain = analyze_redirects(pairs)
    assert chain.length == 1
    assert chain.hops[0].status_code == 301
    assert chain.hops[0].location == "https://b.com/"


def test_final_url_is_last_location():
    pairs = [
        (_req("https://a.com/"), _resp(301, "https://b.com/")),
        (_req("https://b.com/"), _resp(302, "https://c.com/")),
    ]
    chain = analyze_redirects(pairs)
    assert chain.final_url == "https://c.com/"


def test_redirect_loop_detected():
    pairs = [
        (_req("https://a.com/"), _resp(302, "https://b.com/")),
        (_req("https://a.com/"), _resp(302, "https://b.com/")),
    ]
    chain = analyze_redirects(pairs)
    assert chain.is_redirect_loop


def test_no_loop_for_unique_urls():
    pairs = [
        (_req("https://a.com/"), _resp(301, "https://b.com/")),
        (_req("https://b.com/"), _resp(302, "https://c.com/")),
    ]
    chain = analyze_redirects(pairs)
    assert not chain.is_redirect_loop


def test_display_contains_hop_info():
    pairs = [(_req("https://a.com/"), _resp(301, "https://b.com/"))]
    chain = analyze_redirects(pairs)
    text = chain.display()
    assert "301" in text
    assert "https://a.com/" in text
    assert "https://b.com/" in text


def test_to_dict_structure():
    pairs = [(_req("https://a.com/"), _resp(301, "https://b.com/"))]
    chain = analyze_redirects(pairs)
    d = chain.to_dict()
    assert d["length"] == 1
    assert d["final_url"] == "https://b.com/"
    assert isinstance(d["hops"], list)


def test_all_redirect_codes_captured():
    for code in REDIRECT_CODES:
        pairs = [(_req(), _resp(code, "https://next.com/"))]
        chain = analyze_redirects(pairs)
        assert chain.length == 1
