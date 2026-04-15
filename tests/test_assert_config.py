"""Tests for loading and saving assertion rule configs."""
import json
import pytest
from pathlib import Path

from req_replay.assert_config import load_rules, save_rules, rules_to_dict, rules_from_dict
from req_replay.assert_rules import AssertionRule


SAMPLE_RULES = [
    AssertionRule(field="status", operator="eq", expected=200),
    AssertionRule(field="body_contains", operator="contains", expected="ok"),
    AssertionRule(field="header:x-api", operator="eq", expected="v1"),
]


def test_rules_to_dict():
    data = rules_to_dict(SAMPLE_RULES)
    assert len(data) == 3
    assert data[0] == {"field": "status", "operator": "eq", "expected": 200}


def test_rules_from_dict_roundtrip():
    data = rules_to_dict(SAMPLE_RULES)
    restored = rules_from_dict(data)
    assert len(restored) == len(SAMPLE_RULES)
    for orig, rest in zip(SAMPLE_RULES, restored):
        assert rest.field == orig.field
        assert rest.operator == orig.operator
        assert rest.expected == orig.expected


def test_save_and_load_rules(tmp_path):
    config_path = tmp_path / "rules.json"
    save_rules(SAMPLE_RULES, config_path)
    assert config_path.exists()
    loaded = load_rules(config_path)
    assert len(loaded) == len(SAMPLE_RULES)
    assert loaded[1].field == "body_contains"


def test_save_creates_parent_dirs(tmp_path):
    config_path = tmp_path / "nested" / "dir" / "rules.json"
    save_rules(SAMPLE_RULES, config_path)
    assert config_path.exists()


def test_load_raises_for_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_rules(tmp_path / "nonexistent.json")


def test_load_raises_for_invalid_format(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"not": "a list"}))
    with pytest.raises(ValueError):
        load_rules(bad)
