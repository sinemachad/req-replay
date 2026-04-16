"""Generate status badge data for a collection of replay results."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence


@dataclass
class BadgeData:
    label: str
    message: str
    color: str

    def to_dict(self) -> dict:
        return {"label": self.label, "message": self.message, "color": self.color}

    def to_shields_url(self) -> str:
        base = "https://img.shields.io/badge"
        label = self.label.replace("-", "--").replace("_", "__").replace(" ", "_")
        message = self.message.replace("-", "--").replace("_", "__").replace(" ", "_")
        return f"{base}/{label}-{message}-{self.color}"


def generate_badge(results: Sequence[object], label: str = "replay") -> BadgeData:
    """Generate badge data from a sequence of objects with a ``passed`` bool attribute."""
    if not results:
        return BadgeData(label=label, message="no results", color="lightgrey")

    total = len(results)
    passed = sum(1 for r in results if getattr(r, "passed", False))
    failed = total - passed

    if failed == 0:
        message = f"{total} passed"
        color = "brightgreen"
    elif passed == 0:
        message = f"{total} failed"
        color = "red"
    else:
        message = f"{passed}/{total} passed"
        color = "yellow"

    return BadgeData(label=label, message=message, color=color)
