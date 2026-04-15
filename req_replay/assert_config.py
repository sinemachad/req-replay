"""Load and save assertion rule sets from/to JSON files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from req_replay.assert_rules import AssertionRule


def rules_to_dict(rules: list[AssertionRule]) -> list[dict[str, Any]]:
    return [
        {"field": r.field, "operator": r.operator, "expected": r.expected}
        for r in rules
    ]


def rules_from_dict(data: list[dict[str, Any]]) -> list[AssertionRule]:
    return [
        AssertionRule(
            field=item["field"],
            operator=item["operator"],
            expected=item["expected"],
        )
        for item in data
    ]


def save_rules(rules: list[AssertionRule], path: Path) -> None:
    """Persist assertion rules to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rules_to_dict(rules), fh, indent=2)


def load_rules(path: Path) -> list[AssertionRule]:
    """Load assertion rules from a JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Assertion config not found: {path}")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("Assertion config must be a JSON array.")
    return rules_from_dict(data)
