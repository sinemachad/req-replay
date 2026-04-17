"""Baseline management: save and compare responses against a stored baseline."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from req_replay.models import CapturedResponse, to_dict, from_dict
from req_replay.diff import diff_responses, DiffResult


def _baseline_path(store_dir: Path, request_id: str) -> Path:
    return store_dir / "baselines" / f"{request_id}.json"


def save_baseline(store_dir: Path, request_id: str, response: CapturedResponse) -> Path:
    path = _baseline_path(store_dir, request_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_dict(response), indent=2))
    return path


def load_baseline(store_dir: Path, request_id: str) -> CapturedResponse:
    path = _baseline_path(store_dir, request_id)
    if not path.exists():
        raise FileNotFoundError(f"No baseline for request '{request_id}'")
    return from_dict(json.loads(path.read_text()))


def delete_baseline(store_dir: Path, request_id: str) -> bool:
    path = _baseline_path(store_dir, request_id)
    if path.exists():
        path.unlink()
        return True
    return False


def list_baselines(store_dir: Path) -> list[str]:
    base = store_dir / "baselines"
    if not base.exists():
        return []
    return [p.stem for p in sorted(base.glob("*.json"))]


@dataclass
class BaselineResult:
    request_id: str
    diff: DiffResult

    @property
    def passed(self) -> bool:
        return self.diff.is_identical

    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] baseline check for {self.request_id}: {self.diff.summary()}"


def compare_to_baseline(
    store_dir: Path,
    request_id: str,
    actual: CapturedResponse,
    ignore_headers: Optional[list[str]] = None,
) -> BaselineResult:
    baseline = load_baseline(store_dir, request_id)
    diff = diff_responses(baseline, actual, ignore_headers=ignore_headers or [])
    return BaselineResult(request_id=request_id, diff=diff)
