"""Tests for req_replay.baseline."""
from __future__ import annotations

import pytest
from pathlib import Path

from req_replay.models import CapturedResponse
from req_replay.baseline import (
    save_baseline,
    load_baseline,
    delete_baseline,
    list_baselines,
    compare_to_baseline,
    BaselineResult,
)


def _resp(status: int = 200, body: str = '{"ok": true}') -> CapturedResponse:
    return CapturedResponse(
        status_code=status,
        headers={"content-type": "application/json"},
        body=body,
    )


@pytest.fixture()
def store_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_save_creates_file(store_dir: Path) -> None:
    path = save_baseline(store_dir, "req-1", _resp())
    assert path.exists()


def test_load_returns_correct_response(store_dir: Path) -> None:
    save_baseline(store_dir, "req-1", _resp(201, "hello"))
    loaded = load_baseline(store_dir, "req-1")
    assert loaded.status_code == 201
    assert loaded.body == "hello"


def test_load_raises_for_missing(store_dir: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_baseline(store_dir, "no-such-id")


def test_delete_existing(store_dir: Path) -> None:
    save_baseline(store_dir, "req-1", _resp())
    assert delete_baseline(store_dir, "req-1") is True
    assert not _baseline_path_exists(store_dir, "req-1")


def _baseline_path_exists(store_dir: Path, rid: str) -> bool:
    return (store_dir / "baselines" / f"{rid}.json").exists()


def test_delete_missing_returns_false(store_dir: Path) -> None:
    assert delete_baseline(store_dir, "ghost") is False


def test_list_baselines_empty(store_dir: Path) -> None:
    assert list_baselines(store_dir) == []


def test_list_baselines_returns_ids(store_dir: Path) -> None:
    save_baseline(store_dir, "b", _resp())
    save_baseline(store_dir, "a", _resp())
    ids = list_baselines(store_dir)
    assert ids == ["a", "b"]


def test_compare_identical_passes(store_dir: Path) -> None:
    r = _resp()
    save_baseline(store_dir, "req-1", r)
    result = compare_to_baseline(store_dir, "req-1", r)
    assert isinstance(result, BaselineResult)
    assert result.passed
    assert "PASS" in result.summary()


def test_compare_different_status_fails(store_dir: Path) -> None:
    save_baseline(store_dir, "req-1", _resp(200))
    result = compare_to_baseline(store_dir, "req-1", _resp(404))
    assert not result.passed
    assert "FAIL" in result.summary()


def test_compare_missing_baseline_raises(store_dir: Path) -> None:
    with pytest.raises(FileNotFoundError):
        compare_to_baseline(store_dir, "missing", _resp())
