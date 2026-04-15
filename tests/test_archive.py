"""Tests for req_replay.archive."""

from __future__ import annotations

import pytest
from pathlib import Path
from datetime import datetime, timezone

from req_replay.models import CapturedRequest
from req_replay.storage import RequestStore
from req_replay.archive import export_archive, import_archive


def _req(req_id: str) -> CapturedRequest:
    return CapturedRequest(
        id=req_id,
        method="GET",
        url=f"https://example.com/{req_id}",
        headers={"Accept": "application/json"},
        body=None,
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        tags=[],
    )


@pytest.fixture()
def store(tmp_path: Path) -> RequestStore:
    return RequestStore(tmp_path / "store")


def test_export_creates_zip(tmp_path: Path, store: RequestStore) -> None:
    store.save(_req("abc"))
    store.save(_req("def"))
    dest = tmp_path / "out" / "bundle.zip"
    ids = export_archive(store, dest)
    assert dest.exists()
    assert set(ids) == {"abc", "def"}


def test_export_empty_store_creates_empty_zip(tmp_path: Path, store: RequestStore) -> None:
    dest = tmp_path / "empty.zip"
    ids = export_archive(store, dest)
    assert ids == []
    assert dest.exists()


def test_import_restores_requests(tmp_path: Path, store: RequestStore) -> None:
    store.save(_req("r1"))
    store.save(_req("r2"))
    archive = tmp_path / "bundle.zip"
    export_archive(store, archive)

    new_store = RequestStore(tmp_path / "new_store")
    imported = import_archive(archive, new_store)

    assert set(imported) == {"r1", "r2"}
    assert new_store.load("r1").url == "https://example.com/r1"
    assert new_store.load("r2").url == "https://example.com/r2"


def test_import_skips_existing_by_default(tmp_path: Path, store: RequestStore) -> None:
    store.save(_req("r1"))
    archive = tmp_path / "bundle.zip"
    export_archive(store, archive)

    # r1 already exists in store — should be skipped
    imported = import_archive(archive, store)
    assert imported == []


def test_import_overwrites_when_flag_set(tmp_path: Path, store: RequestStore) -> None:
    store.save(_req("r1"))
    archive = tmp_path / "bundle.zip"
    export_archive(store, archive)

    imported = import_archive(archive, store, overwrite=True)
    assert "r1" in imported


def test_import_raises_for_missing_archive(tmp_path: Path, store: RequestStore) -> None:
    with pytest.raises(FileNotFoundError):
        import_archive(tmp_path / "nonexistent.zip", store)
