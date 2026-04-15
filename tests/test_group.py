"""Tests for req_replay.group."""
import pytest

from req_replay.group import (
    create_group,
    add_to_group,
    remove_from_group,
    get_group,
    list_groups,
    resolve_group,
)
from req_replay.models import CapturedRequest
from req_replay.storage import RequestStore


@pytest.fixture()
def store(tmp_path):
    return RequestStore(str(tmp_path / "store"))


@pytest.fixture()
def sample_request():
    return CapturedRequest(
        id="req-001",
        method="GET",
        url="https://example.com/api",
        headers={},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
    )


def test_create_group_returns_group(store):
    g = create_group(store, "smoke")
    assert g.name == "smoke"
    assert g.request_ids == []


def test_create_group_persists(store):
    create_group(store, "smoke", description="smoke tests")
    g = get_group(store, "smoke")
    assert g.description == "smoke tests"


def test_add_to_group_appends_id(store):
    create_group(store, "g1")
    g = add_to_group(store, "g1", "abc")
    assert "abc" in g.request_ids


def test_add_to_group_deduplicates(store):
    create_group(store, "g1")
    add_to_group(store, "g1", "abc")
    g = add_to_group(store, "g1", "abc")
    assert g.request_ids.count("abc") == 1


def test_remove_from_group(store):
    create_group(store, "g1")
    add_to_group(store, "g1", "abc")
    g = remove_from_group(store, "g1", "abc")
    assert "abc" not in g.request_ids


def test_remove_nonexistent_id_is_noop(store):
    create_group(store, "g1")
    g = remove_from_group(store, "g1", "missing")
    assert g.request_ids == []


def test_get_group_raises_for_unknown(store):
    with pytest.raises(KeyError, match="not found"):
        get_group(store, "nope")


def test_list_groups_empty(store):
    assert list_groups(store) == []


def test_list_groups_returns_names(store):
    create_group(store, "alpha")
    create_group(store, "beta")
    names = list_groups(store)
    assert "alpha" in names
    assert "beta" in names


def test_resolve_group_returns_requests(store, sample_request):
    store.save(sample_request)
    create_group(store, "g1")
    add_to_group(store, "g1", sample_request.id)
    requests = resolve_group(store, "g1")
    assert len(requests) == 1
    assert requests[0].id == sample_request.id


def test_resolve_group_skips_missing_ids(store):
    create_group(store, "g1")
    add_to_group(store, "g1", "ghost-id")
    requests = resolve_group(store, "g1")
    assert requests == []
