"""Tests for RetryBudget."""
from __future__ import annotations

import pytest

from req_replay.retry_budget import RetryBudget, BudgetEntry


def test_initial_remaining_equals_max():
    b = RetryBudget(max_total_retries=5)
    assert b.remaining == 5


def test_not_exhausted_initially():
    b = RetryBudget(max_total_retries=3)
    assert not b.exhausted


def test_consume_first_attempt_is_free():
    b = RetryBudget(max_total_retries=5)
    ok = b.consume("r1", attempts=1, succeeded=True)
    assert ok
    assert b.remaining == 5  # 1 attempt = 0 retries


def test_consume_two_attempts_uses_one_retry():
    b = RetryBudget(max_total_retries=5)
    b.consume("r1", attempts=2, succeeded=True)
    assert b.remaining == 4


def test_consume_returns_false_when_budget_exceeded():
    b = RetryBudget(max_total_retries=2)
    b.consume("r1", attempts=3, succeeded=False)  # uses 2
    ok = b.consume("r2", attempts=2, succeeded=True)  # needs 1 more — over budget
    assert not ok


def test_exhausted_after_budget_used():
    b = RetryBudget(max_total_retries=2)
    b.consume("r1", attempts=3, succeeded=False)
    assert b.exhausted


def test_remaining_never_negative():
    b = RetryBudget(max_total_retries=1)
    b.consume("r1", attempts=5, succeeded=False)
    assert b.remaining == 0


def test_entries_recorded():
    b = RetryBudget(max_total_retries=10)
    b.consume("r1", attempts=2, succeeded=True)
    b.consume("r2", attempts=1, succeeded=False)
    entries = b.entries()
    assert len(entries) == 2
    ids = {e["request_id"] for e in entries}
    assert ids == {"r1", "r2"}


def test_summary_string_contains_used():
    b = RetryBudget(max_total_retries=10)
    b.consume("r1", attempts=3, succeeded=True)
    s = b.summary()
    assert "2/10" in s  # 3 attempts = 2 retries
    assert "1/1" in s   # 1 succeeded out of 1


def test_budget_entry_to_dict():
    e = BudgetEntry(request_id="abc", attempts=2, succeeded=True)
    d = e.to_dict()
    assert d == {"request_id": "abc", "attempts": 2, "succeeded": True}
