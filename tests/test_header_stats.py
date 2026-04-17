"""Tests for req_replay.header_stats."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from req_replay.header_stats import analyze_headers, HeaderStats
from req_replay.models import CapturedRequest


def _req(headers: dict) -> CapturedRequest:
    r = MagicMock(spec=CapturedRequest)
    r.headers = headers
    return r


def test_empty_list_returns_zero_stats():
    stats = analyze_headers([])
    assert stats.total_requests == 0
    assert stats.header_frequency == {}


def test_single_request_counts_headers():
    stats = analyze_headers([_req({"Content-Type": "application/json", "Accept": "*/*"})])
    assert stats.total_requests == 1
    assert stats.header_frequency["content-type"] == 1
    assert stats.header_frequency["accept"] == 1


def test_header_keys_normalised_to_lowercase():
    stats = analyze_headers([
        _req({"Authorization": "Bearer abc"}),
        _req({"authorization": "Bearer xyz"}),
    ])
    assert stats.header_frequency["authorization"] == 2


def test_frequency_counts_multiple_requests():
    reqs = [
        _req({"content-type": "application/json"}),
        _req({"content-type": "text/plain"}),
        _req({"accept": "*/*"}),
    ]
    stats = analyze_headers(reqs)
    assert stats.total_requests == 3
    assert stats.header_frequency["content-type"] == 2
    assert stats.header_frequency["accept"] == 1


def test_value_frequency_tracks_distinct_values():
    reqs = [
        _req({"accept": "application/json"}),
        _req({"accept": "application/json"}),
        _req({"accept": "text/html"}),
    ]
    stats = analyze_headers(reqs)
    vals = stats.value_frequency["accept"]
    assert vals["application/json"] == 2
    assert vals["text/html"] == 1


def test_display_contains_header_name():
    stats = analyze_headers([_req({"x-request-id": "abc"})])
    output = stats.display()
    assert "x-request-id" in output
    assert "100.0%" in output


def test_display_zero_requests():
    stats = analyze_headers([])
    output = stats.display()
    assert "0" in output
