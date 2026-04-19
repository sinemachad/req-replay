import pytest
from req_replay.method_stats import analyze_methods, MethodStats
from req_replay.models import CapturedRequest


def _req(method: str) -> CapturedRequest:
    return CapturedRequest(
        id="test",
        method=method,
        url="https://example.com/api",
        headers={},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


def test_empty_list_returns_zero_stats():
    stats = analyze_methods([])
    assert stats.total == 0
    assert stats.counts == {}
    assert stats.percentages == {}


def test_single_get_request():
    stats = analyze_methods([_req("GET")])
    assert stats.total == 1
    assert stats.counts["GET"] == 1
    assert stats.percentages["GET"] == pytest.approx(100.0)


def test_multiple_methods_counted():
    reqs = [_req("GET"), _req("GET"), _req("POST"), _req("DELETE")]
    stats = analyze_methods(reqs)
    assert stats.total == 4
    assert stats.counts["GET"] == 2
    assert stats.counts["POST"] == 1
    assert stats.counts["DELETE"] == 1


def test_percentages_sum_to_100():
    reqs = [_req("GET"), _req("POST"), _req("PUT")]
    stats = analyze_methods(reqs)
    total_pct = sum(stats.percentages.values())
    assert total_pct == pytest.approx(100.0)


def test_method_normalised_to_uppercase():
    stats = analyze_methods([_req("get"), _req("Get")])
    assert "GET" in stats.counts
    assert stats.counts["GET"] == 2


def test_top_returns_n_methods():
    reqs = [_req("GET")] * 5 + [_req("POST")] * 3 + [_req("DELETE")] * 1
    stats = analyze_methods(reqs)
    top2 = stats.top(2)
    assert len(top2) == 2
    assert top2[0] == ("GET", 5)
    assert top2[1] == ("POST", 3)


def test_display_contains_method_name():
    stats = analyze_methods([_req("PATCH"), _req("PATCH")])
    output = stats.display()
    assert "PATCH" in output
    assert "2" in output


def test_display_contains_total():
    stats = analyze_methods([_req("GET")])
    assert "Total requests: 1" in stats.display()
