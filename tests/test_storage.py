"""Tests for the RequestStore storage layer."""

import pytest
from pathlib import Path

from req_replay.models import CapturedRequest
from req_replay.storage import RequestStore


@pytest.fixture
def store(tmp_path):
    return RequestStore(store_dir=tmp_path / "captures")


@pytest.fixture
def sample_request():
    return CapturedRequest(
        method="GET",
        url="https://api.example.com/users",
        headers={"Authorization": "Bearer token123", "Accept": "application/json"},
        query_params={"page": "1", "limit": "10"},
    )


def test_save_creates_file(store, sample_request):
    path = store.save(sample_request)
    assert path.exists()
    assert path.suffix == ".json"


def test_load_returns_correct_request(store, sample_request):
    store.save(sample_request)
    loaded = store.load(sample_request.id)
    assert loaded.id == sample_request.id
    assert loaded.method == sample_request.method
    assert loaded.url == sample_request.url
    assert loaded.headers == sample_request.headers
    assert loaded.query_params == sample_request.query_params


def test_load_raises_for_missing_id(store):
    with pytest.raises(FileNotFoundError, match="nonexistent-id"):
        store.load("nonexistent-id")


def test_list_all_returns_sorted_by_time(store):
    r1 = CapturedRequest(method="GET", url="https://example.com/a", captured_at="2024-01-01T10:00:00")
    r2 = CapturedRequest(method="POST", url="https://example.com/b", captured_at="2024-01-01T11:00:00")
    r3 = CapturedRequest(method="DELETE", url="https://example.com/c", captured_at="2024-01-01T09:00:00")
    for r in [r1, r2, r3]:
        store.save(r)
    results = store.list_all()
    assert len(results) == 3
    assert results[0].url == "https://example.com/c"
    assert results[2].url == "https://example.com/b"


def test_delete_removes_file(store, sample_request):
    store.save(sample_request)
    result = store.delete(sample_request.id)
    assert result is True
    assert not store._request_path(sample_request.id).exists()


def test_delete_returns_false_for_missing(store):
    assert store.delete("does-not-exist") is False


def test_clear_removes_all(store):
    for _ in range(3):
        store.save(CapturedRequest(method="GET", url="https://example.com"))
    count = store.clear()
    assert count == 3
    assert store.list_all() == []
