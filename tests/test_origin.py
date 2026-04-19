"""Tests for req_replay.origin."""
from __future__ import annotations
import pytest
from req_replay.models import CapturedRequest
from req_replay.origin import analyze_origins, OriginStats


def _req(headers: dict | None = None) -> CapturedRequest:
    return CapturedRequest(
        id="test-id",
        method="GET",
        url="https://example.com/api",
        headers=headers or {},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


def test_empty_list_returns_zero_stats():
    stats = analyze_origins([])
    assert stats.total == 0
    assert stats.top_ips == []
    assert stats.top_referers == []
    assert stats.top_user_agents == []


def test_single_request_with_ip():
    req = _req({"X-Forwarded-For": "192.168.1.1"})
    stats = analyze_origins([req])
    assert stats.total == 1
    assert stats.top_ips == [("192.168.1.1", 1)]


def test_ip_extracted_from_x_real_ip():
    req = _req({"X-Real-IP": "10.0.0.5"})
    stats = analyze_origins([req])
    assert stats.top_ips == [("10.0.0.5", 1)]


def test_forwarded_for_takes_first_ip():
    req = _req({"X-Forwarded-For": "1.2.3.4, 5.6.7.8"})
    stats = analyze_origins([req])
    assert stats.top_ips[0][0] == "1.2.3.4"


def test_user_agent_counted():
    req = _req({"User-Agent": "Mozilla/5.0"})
    stats = analyze_origins([req])
    assert stats.top_user_agents == [("Mozilla/5.0", 1)]


def test_referer_counted():
    req = _req({"Referer": "https://google.com"})
    stats = analyze_origins([req])
    assert stats.top_referers == [("https://google.com", 1)]


def test_referrer_alternate_spelling():
    req = _req({"Referrer": "https://bing.com"})
    stats = analyze_origins([req])
    assert stats.top_referers == [("https://bing.com", 1)]


def test_top_n_limits_results():
    reqs = [_req({"User-Agent": f"agent-{i}"}) for i in range(10)]
    stats = analyze_origins(reqs, top_n=3)
    assert len(stats.top_user_agents) == 3


def test_most_common_ip_ranked_first():
    reqs = [
        _req({"X-Forwarded-For": "1.1.1.1"}),
        _req({"X-Forwarded-For": "1.1.1.1"}),
        _req({"X-Forwarded-For": "2.2.2.2"}),
    ]
    stats = analyze_origins(reqs)
    assert stats.top_ips[0] == ("1.1.1.1", 2)


def test_display_contains_total():
    req = _req({"X-Forwarded-For": "9.9.9.9"})
    stats = analyze_origins([req])
    assert "Total requests: 1" in stats.display()


def test_display_contains_ip_section():
    req = _req({"X-Forwarded-For": "9.9.9.9"})
    stats = analyze_origins([req])
    output = stats.display()
    assert "9.9.9.9" in output
    assert "Top IPs" in output
