"""Utilities for diffing captured vs replayed HTTP responses."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from req_replay.models import CapturedResponse


@dataclass
class DiffResult:
    status_match: bool
    body_match: bool
    header_diffs: dict[str, tuple[str | None, str | None]]
    original_status: int
    replayed_status: int
    original_body: str
    replayed_body: str

    @property
    def is_identical(self) -> bool:
        return self.status_match and self.body_match and not self.header_diffs

    def summary(self) -> str:
        lines = []
        if not self.status_match:
            lines.append(
                f"  STATUS  original={self.original_status}  replayed={self.replayed_status}"
            )
        if not self.body_match:
            lines.append("  BODY    mismatch detected")
            lines.append(f"    original : {self.original_body[:120]}")
            lines.append(f"    replayed : {self.replayed_body[:120]}")
        for header, (orig, replay) in self.header_diffs.items():
            lines.append(f"  HEADER  {header}: original={orig!r}  replayed={replay!r}")
        if not lines:
            return "Responses are identical."
        return "Differences found:\n" + "\n".join(lines)


def _normalise_body(body: str) -> Any:
    """Try to parse body as JSON for semantic comparison; fall back to raw string."""
    try:
        return json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return body


def diff_responses(
    original: CapturedResponse,
    replayed: CapturedResponse,
    ignore_headers: list[str] | None = None,
) -> DiffResult:
    """Compare two CapturedResponse objects and return a DiffResult."""
    ignore = {h.lower() for h in (ignore_headers or [])}
    ignore.update({"date", "x-request-id", "x-response-time"})

    status_match = original.status_code == replayed.status_code
    body_match = _normalise_body(original.body) == _normalise_body(replayed.body)

    orig_headers = {k.lower(): v for k, v in original.headers.items()}
    replay_headers = {k.lower(): v for k, v in replayed.headers.items()}
    all_keys = (orig_headers.keys() | replay_headers.keys()) - ignore

    header_diffs: dict[str, tuple[str | None, str | None]] = {}
    for key in sorted(all_keys):
        ov, rv = orig_headers.get(key), replay_headers.get(key)
        if ov != rv:
            header_diffs[key] = (ov, rv)

    return DiffResult(
        status_match=status_match,
        body_match=body_match,
        header_diffs=header_diffs,
        original_status=original.status_code,
        replayed_status=replayed.status_code,
        original_body=original.body or "",
        replayed_body=replayed.body or "",
    )
