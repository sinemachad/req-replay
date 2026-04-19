"""Tests for req_replay.entropy."""
from __future__ import annotations
import pytest
from req_replay.entropy import _shannon, analyze_entropy, EntropyResult, DEFAULT_THRESHOLD
from req_replay.models import CapturedRequest


def _req(headers: dict | None = None, url: str = "https://example.com/api") -> CapturedRequest:
    return CapturedRequest(
        id="test-1",
        method="GET",
        url=url,
        headers=headers or {},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


def test_shannon_empty_string_is_zero():
    assert _shannon("") == 0.0


def test_shannon_uniform_string():
    # "aaaa" has entropy 0
    assert _shannon("aaaa") == pytest.approx(0.0)


def test_shannon_two_chars_equal():
    assert _shannon("ab") == pytest.approx(1.0)


def test_shannon_high_entropy_random_like():
    val = "aB3$xQzP9mLkRv2!"
    assert _shannon(val) > 3.5


def test_clean_request_passes():
    req = _req(headers={"Content-Type": "application/json"})
    result = analyze_entropy(req)
    assert result.passed()


def test_high_entropy_header_flagged():
    secret = "aB3xQzP9mLkRv2wYnJhTqDcSuFeGbViO"
    req = _req(headers={"Authorization": f"Bearer {secret}"})
    result = analyze_entropy(req, threshold=4.0)
    assert not result.passed()
    locations = [h.location for h in result.hits]
    assert "header:Authorization" in locations


def test_high_entropy_query_param_flagged():
    token = "aB3xQzP9mLkRv2wYnJhTqDcSuFeGbViO"
    req = _req(url=f"https://example.com/api?token={token}")
    result = analyze_entropy(req, threshold=4.0)
    assert not result.passed()
    locations = [h.location for h in result.hits]
    assert "query:token" in locations


def test_summary_clean():
    req = _req()
    result = analyze_entropy(req)
    assert "No high-entropy" in result.summary()


def test_summary_with_hits():
    secret = "aB3xQzP9mLkRv2wYnJhTqDcSuFeGbViO"
    req = _req(headers={"X-Api-Key": secret})
    result = analyze_entropy(req, threshold=4.0)
    assert not result.passed()
    s = result.summary()
    assert "X-Api-Key" in s


def test_to_dict_masks_value():
    secret = "aB3xQzP9mLkRv2wYnJhTqDcSuFeGbViO"
    req = _req(headers={"X-Secret": secret})
    result = analyze_entropy(req, threshold=4.0)
    d = result.hits[0].to_dict()
    assert d["value"].endswith("...")
    assert len(d["value"]) == 9  # 6 chars + "..."
