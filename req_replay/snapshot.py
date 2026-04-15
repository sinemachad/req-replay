"""Snapshot testing: save a response as a baseline and compare future replays against it."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from req_replay.models import CapturedResponse, to_dict as resp_to_dict, from_dict as resp_from_dict
from req_replay.diff import diff_responses, DiffResult


_SNAPSHOT_DIR = Path(".req_replay_snapshots")


def _snapshot_path(snapshot_id: str, base_dir: Path = _SNAPSHOT_DIR) -> Path:
    return base_dir / f"{snapshot_id}.json"


def save_snapshot(
    snapshot_id: str,
    response: CapturedResponse,
    base_dir: Path = _SNAPSHOT_DIR,
) -> Path:
    """Persist *response* as the baseline snapshot for *snapshot_id*."""
    path = _snapshot_path(snapshot_id, base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(resp_to_dict(response), indent=2))
    return path


def load_snapshot(
    snapshot_id: str,
    base_dir: Path = _SNAPSHOT_DIR,
) -> CapturedResponse:
    """Load a previously saved baseline snapshot."""
    path = _snapshot_path(snapshot_id, base_dir)
    if not path.exists():
        raise FileNotFoundError(f"No snapshot found for id '{snapshot_id}' at {path}")
    return resp_from_dict(json.loads(path.read_text()))


def delete_snapshot(
    snapshot_id: str,
    base_dir: Path = _SNAPSHOT_DIR,
) -> bool:
    """Remove a snapshot file.  Returns True if it existed."""
    path = _snapshot_path(snapshot_id, base_dir)
    if path.exists():
        path.unlink()
        return True
    return False


@dataclass
class SnapshotResult:
    snapshot_id: str
    diff: DiffResult
    created: bool = False  # True when the snapshot was just initialised

    @property
    def passed(self) -> bool:
        return self.created or self.diff.is_identical

    @property
    def summary(self) -> str:
        if self.created:
            return f"[snapshot:{self.snapshot_id}] baseline created"
        status = "PASS" if self.passed else "FAIL"
        return f"[snapshot:{self.snapshot_id}] {status} — {self.diff.summary}"


def assert_snapshot(
    snapshot_id: str,
    response: CapturedResponse,
    base_dir: Path = _SNAPSHOT_DIR,
    update: bool = False,
) -> SnapshotResult:
    """Compare *response* against the stored baseline.

    If no baseline exists (or *update* is True) the current response is saved
    as the new baseline and the result is marked as *created*.
    """
    path = _snapshot_path(snapshot_id, base_dir)
    if update or not path.exists():
        save_snapshot(snapshot_id, response, base_dir)
        dummy_diff = diff_responses(response, response)
        return SnapshotResult(snapshot_id=snapshot_id, diff=dummy_diff, created=True)

    baseline = load_snapshot(snapshot_id, base_dir)
    diff = diff_responses(baseline, response)
    return SnapshotResult(snapshot_id=snapshot_id, diff=diff)
