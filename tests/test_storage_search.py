"""Integration tests for RequestStore.search() using FilterCriteria."""
import pytest
from datetime import datetime, timezone
from pathlib import Path

from req_replay.models import CapturedRequest
from req_replay.storage import RequestStore
from req_replay.filter import FilterCriteria


def _req(rid: str, method: str, url: str, tags: list) -> CapturedRequest:
    return CapturedRequest(
        id=rid,
        method=method,
        url=url,
        headers={},
        body=None,
        timestamp=datetime.now(timezone.utc).isoformat(),
        tags=tags,
    )


@pytest.fixture()
def store(tmp_path: Path) -> RequestStore:
    s = RequestStore(base_dir=tmp_path)
    s.save(_req("r1", "GET",    "https://api.example.com/users",    ["smoke"]))
    s.save(_req("r2", "POST",   "https://api.example.com/users",    ["smoke", "auth"]))
    s.save(_req("r3", "GET",    "https://other.io/health",          []))
    s.save(_req("r4", "DELETE", "https://api.example.com/users/99", ["auth"]))
    return s


def test_search_no_criteria_returns_all(store: RequestStore):
    assert len(store.search()) == 4


def test_search_by_method(store: RequestStore):
    result = store.search(FilterCriteria(method="GET"))
    assert len(result) == 2
    assert all(r.method == "GET" for r in result)


def test_search_by_host(store: RequestStore):
    result = store.search(FilterCriteria(host="other.io"))
    assert len(result) == 1
    assert result[0].id == "r3"


def test_search_by_tag(store: RequestStore):
    result = store.search(FilterCriteria(tags=["auth"]))
    ids = {r.id for r in result}
    assert ids == {"r2", "r4"}


def test_search_combined(store: RequestStore):
    result = store.search(FilterCriteria(method="GET", tags=["smoke"]))
    assert len(result) == 1
    assert result[0].id == "r1"


def test_search_no_match_returns_empty(store: RequestStore):
    result = store.search(FilterCriteria(method="PATCH"))
    assert result == []


def test_search_with_explicit_none_criteria(store: RequestStore):
    """Passing criteria=None explicitly behaves like list_all."""
    assert len(store.search(criteria=None)) == 4
