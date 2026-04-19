"""Tests for req_replay.dns."""
from __future__ import annotations

from unittest.mock import patch
import socket

import pytest

from req_replay.dns import DNSResult, resolve_host, analyze_dns
from req_replay.models import CapturedRequest


def _req(url: str) -> CapturedRequest:
    return CapturedRequest(
        id="abc",
        method="GET",
        url=url,
        headers={},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


_FAKE_ADDRINFO = [
    (socket.AF_INET, socket.SOCK_STREAM, 0, "", ("93.184.216.34", 0)),
    (socket.AF_INET6, socket.SOCK_STREAM, 0, "", ("2606:2800:220:1:248:1893:25c8:1946", 0, 0, 0)),
]


def test_dns_result_reachable_when_ips_present():
    r = DNSResult(host="example.com", resolved=["93.184.216.34"])
    assert r.reachable is True


def test_dns_result_not_reachable_when_empty():
    r = DNSResult(host="example.com", resolved=[])
    assert r.reachable is False


def test_dns_result_display_contains_host():
    r = DNSResult(host="example.com", resolved=["1.2.3.4"])
    assert "example.com" in r.display()


def test_dns_result_display_shows_error():
    r = DNSResult(host="bad.invalid", error="Name or service not known")
    assert "Error" in r.display()


def test_resolve_host_success():
    with patch("req_replay.dns.socket.getaddrinfo", return_value=_FAKE_ADDRINFO):
        result = resolve_host("example.com")
    assert result.host == "example.com"
    assert "93.184.216.34" in result.resolved
    assert result.error is None


def test_resolve_host_failure():
    with patch("req_replay.dns.socket.getaddrinfo", side_effect=socket.gaierror("fail")):
        result = resolve_host("bad.invalid")
    assert result.reachable is False
    assert result.error is not None


def test_analyze_dns_deduplicates_hosts():
    reqs = [
        _req("https://example.com/a"),
        _req("https://example.com/b"),
        _req("https://other.com/c"),
    ]
    with patch("req_replay.dns.socket.getaddrinfo", return_value=_FAKE_ADDRINFO):
        results = analyze_dns(reqs)
    hosts = [r.host for r in results]
    assert len(hosts) == 2
    assert "example.com" in hosts
    assert "other.com" in hosts


def test_analyze_dns_empty_list():
    results = analyze_dns([])
    assert results == []
