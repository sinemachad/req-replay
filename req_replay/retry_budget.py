"""Retry budget tracking: limit total retries across a session."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class BudgetEntry:
    request_id: str
    attempts: int
    succeeded: bool

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "attempts": self.attempts,
            "succeeded": self.succeeded,
        }


@dataclass
class RetryBudget:
    max_total_retries: int = 10
    _used: int = field(default=0, init=False, repr=False)
    _entries: Dict[str, BudgetEntry] = field(default_factory=dict, init=False, repr=False)

    @property
    def remaining(self) -> int:
        return max(0, self.max_total_retries - self._used)

    @property
    def exhausted(self) -> bool:
        return self._used >= self.max_total_retries

    def consume(self, request_id: str, attempts: int, succeeded: bool) -> bool:
        """Record retry attempts. Returns False if budget exceeded."""
        extra = max(0, attempts - 1)  # first attempt is free
        if self._used + extra > self.max_total_retries:
            return False
        self._used += extra
        self._entries[request_id] = BudgetEntry(
            request_id=request_id,
            attempts=attempts,
            succeeded=succeeded,
        )
        return True

    def summary(self) -> str:
        total = len(self._entries)
        succeeded = sum(1 for e in self._entries.values() if e.succeeded)
        return (
            f"RetryBudget: {self._used}/{self.max_total_retries} retries used, "
            f"{succeeded}/{total} requests succeeded"
        )

    def entries(self) -> list:
        return [e.to_dict() for e in self._entries.values()]
