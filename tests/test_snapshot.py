"""Tests for req_replay.snapshot."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from req_replay.models import CapturedResponse
from req_replay.snapshot import (
    save_snapshot,
    load_snapshot,
    delete_snapshot,
    assert_snapshot,
    SnapshotResult,
)


def _resp(status: int = 200, body: str = '{"ok": true}') -> CapturedResponse:
    return CapturedResponse(
        status_code=status,
        headers={"content-type": "application/json"},
        body=body,
        elapsed_ms=42.0,
    )


def test_save_creates_file(tmp_path: Path) -> None:
    save_snapshot("snap1", _resp(), base_dir=tmp_path)
    assert (tmp_path / "snap1.json").exists()


def test_load_returns_correct_response(tmp_path: Path) -> None:
    resp = _resp(status=201, body='{"created": true}')
    save_snapshot("snap2", resp, base_dir=tmp_path)
    loaded = load_snapshot("snap2", base_dir=tmp_path)
    assert loaded.status_code == 201
    assert loaded.body == '{"created": true}'


def test_load_raises_for_missing_snapshot(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="no_such"):
        load_snapshot("no_such", base_dir=tmp_path)


def test_delete_existing_snapshot(tmp_path: Path) -> None:
    save_snapshot("snap3", _resp(), base_dir=tmp_path)
    assert delete_snapshot("snap3", base_dir=tmp_path) is True
    assert not (tmp_path / "snap3.json").exists()


def test_delete_missing_snapshot_returns_false(tmp_path: Path) -> None:
    assert delete_snapshot("ghost", base_dir=tmp_path) is False


def test_assert_snapshot_creates_baseline_on_first_run(tmp_path: Path) -> None:
    result = assert_snapshot("new_snap", _resp(), base_dir=tmp_path)
    assert result.created is True
    assert result.passed is True
    assert "baseline created" in result.summary


def test_assert_snapshot_passes_for_identical_response(tmp_path: Path) -> None:
    resp = _resp()
    assert_snapshot("check", resp, base_dir=tmp_path)  # create baseline
    result = assert_snapshot("check", resp, base_dir=tmp_path)
    assert result.created is False
    assert result.passed is True
    assert "PASS" in result.summary


def test_assert_snapshot_fails_for_changed_status(tmp_path: Path) -> None:
    assert_snapshot("status_check", _resp(status=200), base_dir=tmp_path)
    result = assert_snapshot("status_check", _resp(status=500), base_dir=tmp_path)
    assert result.passed is False
    assert "FAIL" in result.summary


def test_assert_snapshot_update_overwrites_baseline(tmp_path: Path) -> None:
    assert_snapshot("upd", _resp(status=200), base_dir=tmp_path)
    result = assert_snapshot("upd", _resp(status=404), base_dir=tmp_path, update=True)
    assert result.created is True
    loaded = load_snapshot("upd", base_dir=tmp_path)
    assert loaded.status_code == 404
