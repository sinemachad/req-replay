"""Tests for req_replay.badge."""
from dataclasses import dataclass
from req_replay.badge import BadgeData, generate_badge


@dataclass
class _Result:
    passed: bool


def test_all_passed_is_brightgreen():
    results = [_Result(True), _Result(True), _Result(True)]
    badge = generate_badge(results)
    assert badge.color == "brightgreen"
    assert badge.message == "3 passed"


def test_all_failed_is_red():
    results = [_Result(False), _Result(False)]
    badge = generate_badge(results)
    assert badge.color == "red"
    assert badge.message == "2 failed"


def test_mixed_is_yellow():
    results = [_Result(True), _Result(False), _Result(True)]
    badge = generate_badge(results)
    assert badge.color == "yellow"
    assert badge.message == "2/3 passed"


def test_empty_results_returns_lightgrey():
    badge = generate_badge([])
    assert badge.color == "lightgrey"
    assert badge.message == "no results"


def test_custom_label():
    badge = generate_badge([_Result(True)], label="ci")
    assert badge.label == "ci"


def test_to_dict_has_required_keys():
    badge = BadgeData(label="replay", message="3 passed", color="brightgreen")
    d = badge.to_dict()
    assert set(d.keys()) == {"label", "message", "color"}


def test_shields_url_format():
    badge = BadgeData(label="replay", message="3 passed", color="brightgreen")
    url = badge.to_shields_url()
    assert url.startswith("https://img.shields.io/badge/")
    assert "brightgreen" in url


def test_shields_url_escapes_spaces():
    badge = BadgeData(label="my label", message="ok", color="green")
    url = badge.to_shields_url()
    assert " " not in url
