"""Assertion rules for validating replayed responses against expectations."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from req_replay.models import CapturedResponse


@dataclass
class AssertionRule:
    """A single assertion rule applied to a CapturedResponse."""
    field: str          # 'status', 'header:<name>', 'body_contains', 'body_json:<key>'
    operator: str       # 'eq', 'ne', 'contains', 'matches', 'lt', 'gt'
    expected: Any

    def evaluate(self, response: CapturedResponse) -> "AssertionResult":
        actual = self._extract(response)
        passed = self._compare(actual)
        return AssertionResult(
            rule=self,
            actual=actual,
            passed=passed,
        )

    def _extract(self, response: CapturedResponse) -> Any:
        if self.field == "status":
            return response.status_code
        if self.field.startswith("header:"):
            name = self.field.split(":", 1)[1].lower()
            for k, v in response.headers.items():
                if k.lower() == name:
                    return v
            return None
        if self.field == "body_contains":
            return response.body or ""
        if self.field.startswith("body_json:"):
            import json
            key = self.field.split(":", 1)[1]
            try:
                data = json.loads(response.body or "{}")
                return data.get(key)
            except (ValueError, AttributeError):
                return None
        return None

    def _compare(self, actual: Any) -> bool:
        exp = self.expected
        if self.operator == "eq":
            return actual == exp
        if self.operator == "ne":
            return actual != exp
        if self.operator == "contains":
            return exp in (actual or "")
        if self.operator == "matches":
            return bool(re.search(exp, str(actual or "")))
        if self.operator == "lt":
            return actual is not None and actual < exp
        if self.operator == "gt":
            return actual is not None and actual > exp
        return False


@dataclass
class AssertionResult:
    rule: AssertionRule
    actual: Any
    passed: bool

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return (
            f"[{status}] {self.rule.field} {self.rule.operator} "
            f"{self.rule.expected!r} (got {self.actual!r})"
        )


def evaluate_rules(
    response: CapturedResponse,
    rules: list[AssertionRule],
) -> list[AssertionResult]:
    """Evaluate all rules against a response and return results."""
    return [rule.evaluate(response) for rule in rules]
