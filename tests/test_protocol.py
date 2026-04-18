"""Tests for req_replay.protocol."""
from __future__ import annotations

import pytest

from req_replay.models import CapturedRequest
from req_replay.protocol import ProtocolStats, _extract_protocol, analyze_protocols


def _req(url: str = "https://example.com", meta: dict | None = None) -> CapturedRequest:
    return CapturedRequest(
        id="abc",
        method="GET",
        url=url,
        headers={},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata=meta or {},
    )


def test_empty_list_returns_zero_stats():
    stats = analyze_protocols([])
    assert stats.total == 0
    assert stats.version_counts == {}
    assert stats.most_common is None


def test_single_request_counted():
    req = _req(meta={"http_version": "HTTP/2"})
    stats = analyze_protocols([req])
    assert stats.total == 1
    assert stats.version_counts["HTTP/2"] == 1
    assert stats.most_common == "HTTP/2"


def test_multiple_versions_counted():
    reqs = [
        _req(meta={"http_version": "HTTP/1.1"}),
        _req(meta={"http_version": "HTTP/1.1"}),
        _req(meta={"http_version": "HTTP/2"}),
    ]
    stats = analyze_protocols(reqs)
    assert stats.version_counts["HTTP/1.1"] == 2
    assert stats.version_counts["HTTP/2"] == 1
    assert stats.most_common == "HTTP/1.1"


def test_missing_metadata_defaults_to_http11():
    req = _req(meta={})
    version = _extract_protocol(req)
    assert version == "HTTP/1.1"


def test_protocol_key_uppercased():
    req = _req(meta={"http_version": "http/2"})
    version = _extract_protocol(req)
    assert version == "HTTP/2"


def test_display_contains_version():
    req = _req(meta={"http_version": "HTTP/2"})
    stats = analyze_protocols([req])
    output = stats.display()
    assert "HTTP/2" in output
    assert "1" in output


def test_display_empty():
    stats = analyze_protocols([])
    assert "No requests" in stats.display()
