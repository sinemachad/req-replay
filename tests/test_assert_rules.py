"""Tests for assertion rule evaluation."""
import pytest

from req_replay.assert_rules import AssertionRule, evaluate_rules
from req_replay.models import CapturedResponse


def _resp(**kwargs) -> CapturedResponse:
    defaults = dict(
        status_code=200,
        headers={"Content-Type": "application/json"},
        body='{"id": 1, "name": "alice"}',
        elapsed_ms=42.0,
    )
    defaults.update(kwargs)
    return CapturedResponse(**defaults)


def test_status_eq_pass():
    rule = AssertionRule(field="status", operator="eq", expected=200)
    result = rule.evaluate(_resp())
    assert result.passed


def test_status_eq_fail():
    rule = AssertionRule(field="status", operator="eq", expected=404)
    result = rule.evaluate(_resp(status_code=200))
    assert not result.passed


def test_status_lt():
    rule = AssertionRule(field="status", operator="lt", expected=300)
    assert rule.evaluate(_resp(status_code=200)).passed
    assert not rule.evaluate(_resp(status_code=400)).passed


def test_header_eq():
    rule = AssertionRule(field="header:content-type", operator="eq", expected="application/json")
    assert rule.evaluate(_resp()).passed


def test_header_missing_returns_none():
    rule = AssertionRule(field="header:x-missing", operator="eq", expected="something")
    result = rule.evaluate(_resp())
    assert not result.passed
    assert result.actual is None


def test_body_contains_pass():
    rule = AssertionRule(field="body_contains", operator="contains", expected="alice")
    assert rule.evaluate(_resp()).passed


def test_body_contains_fail():
    rule = AssertionRule(field="body_contains", operator="contains", expected="bob")
    assert not rule.evaluate(_resp()).passed


def test_body_json_key():
    rule = AssertionRule(field="body_json:name", operator="eq", expected="alice")
    assert rule.evaluate(_resp()).passed


def test_body_json_key_missing():
    rule = AssertionRule(field="body_json:missing", operator="eq", expected="x")
    result = rule.evaluate(_resp())
    assert not result.passed


def test_body_matches_regex():
    rule = AssertionRule(field="body_contains", operator="matches", expected=r"\"id\":\s*\d+")
    assert rule.evaluate(_resp()).passed


def test_evaluate_rules_returns_all():
    rules = [
        AssertionRule("status", "eq", 200),
        AssertionRule("body_contains", "contains", "alice"),
        AssertionRule("status", "eq", 500),
    ]
    results = evaluate_rules(_resp(), rules)
    assert len(results) == 3
    assert results[0].passed
    assert results[1].passed
    assert not results[2].passed


def test_assertion_result_str_pass():
    rule = AssertionRule("status", "eq", 200)
    result = rule.evaluate(_resp())
    assert "PASS" in str(result)


def test_assertion_result_str_fail():
    rule = AssertionRule("status", "eq", 999)
    result = rule.evaluate(_resp())
    assert "FAIL" in str(result)
