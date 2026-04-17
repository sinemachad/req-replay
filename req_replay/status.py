"""Analyse HTTP status code distribution across captured requests."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from req_replay.models import CapturedRequest, CapturedResponse


@dataclass
class StatusStats:
    total: int
    by_code: Dict[int, int] = field(default_factory=dict)
    by_class: Dict[str, int] = field(default_factory=dict)

    def display(self) -> str:
        if self.total == 0:
            return "No responses recorded."
        lines = [f"Total: {self.total}"]
        lines.append("By class:")
        for cls in sorted(self.by_class):
            lines.append(f"  {cls}: {self.by_class[cls]}")
        lines.append("By code:")
        for code in sorted(self.by_code):
            lines.append(f"  {code}: {self.by_code[code]}")
        return "\n".join(lines)


def _class_label(status: int) -> str:
    if 100 <= status < 200:
        return "1xx informational"
    if 200 <= status < 300:
        return "2xx success"
    if 300 <= status < 400:
        return "3xx redirection"
    if 400 <= status < 500:
        return "4xx client error"
    if 500 <= status < 600:
        return "5xx server error"
    return "unknown"


def analyze_status(
    pairs: List[Tuple[CapturedRequest, CapturedResponse]],
) -> StatusStats:
    if not pairs:
        return StatusStats(total=0)

    codes: List[int] = [resp.status_code for _, resp in pairs]
    by_code: Dict[int, int] = dict(Counter(codes))
    by_class: Dict[str, int] = {}
    for code in codes:
        label = _class_label(code)
        by_class[label] = by_class.get(label, 0) + 1

    return StatusStats(total=len(codes), by_code=by_code, by_class=by_class)
