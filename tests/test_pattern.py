"""Tests for req_replay.pattern."""
import pytest
from req_replay.pattern import normalise_path, analyze_patterns, PatternStats
from req_replay.models import CapturedRequest


def _req(method: str, url: str) -> CapturedRequest:
    return CapturedRequest(
        id='abc',
        method=method,
        url=url,
        headers={},
        body=None,
        timestamp='2024-01-01T00:00:00',
        tags=[],
        metadata={},
    )


def test_normalise_plain_path():
    assert normalise_path('/api/users') == '/api/users'


def test_normalise_int_id():
    assert normalise_path('/api/users/42') == '/api/users/{id}'


def test_normalise_uuid():
    uuid = '123e4567-e89b-12d3-a456-426614174000'
    assert normalise_path(f'/api/items/{uuid}') == '/api/items/{uuid}'


def test_normalise_mixed_segments():
    assert normalise_path('/v1/orders/99/lines/1') == '/v1/orders/{id}/lines/{id}'


def test_analyze_empty_list():
    stats = analyze_patterns([])
    assert stats.total == 0
    assert stats.patterns == {}
    assert stats.top_n == []


def test_analyze_single_request():
    stats = analyze_patterns([_req('GET', 'https://example.com/api/users')])
    assert stats.total == 1
    assert 'GET /api/users' in stats.patterns


def test_analyze_groups_dynamic_ids():
    reqs = [
        _req('GET', 'https://example.com/api/users/1'),
        _req('GET', 'https://example.com/api/users/2'),
        _req('GET', 'https://example.com/api/users/3'),
    ]
    stats = analyze_patterns(reqs)
    assert stats.patterns.get('GET /api/users/{id}') == 3


def test_analyze_top_n_limited():
    reqs = [_req('GET', f'https://example.com/path/{i}') for i in range(20)]
    stats = analyze_patterns(reqs, top=5)
    assert len(stats.top_n) <= 5


def test_analyze_counts_methods_separately():
    reqs = [
        _req('GET', 'https://example.com/api/items'),
        _req('POST', 'https://example.com/api/items'),
        _req('GET', 'https://example.com/api/items'),
    ]
    stats = analyze_patterns(reqs)
    assert stats.patterns['GET /api/items'] == 2
    assert stats.patterns['POST /api/items'] == 1


def test_display_contains_total():
    stats = analyze_patterns([_req('DELETE', 'https://example.com/res/5')])
    out = stats.display()
    assert 'Total requests: 1' in out
    assert 'DELETE /res/{id}' in out
