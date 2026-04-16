"""Tests for req_replay.env."""
from __future__ import annotations

import pytest
from pathlib import Path

from req_replay.env import (
    EnvProfile,
    save_profile,
    load_profile,
    list_profiles,
    delete_profile,
    apply_profile,
)


@pytest.fixture
def base(tmp_path: Path) -> Path:
    return tmp_path


def test_save_and_load_profile(base):
    profile = EnvProfile(name="staging", variables={"HOST": "staging.example.com"})
    save_profile(base, profile)
    loaded = load_profile(base, "staging")
    assert loaded.name == "staging"
    assert loaded.variables["HOST"] == "staging.example.com"


def test_load_missing_profile_raises(base):
    with pytest.raises(FileNotFoundError):
        load_profile(base, "nonexistent")


def test_list_profiles_empty(base):
    assert list_profiles(base) == []


def test_list_profiles_returns_names(base):
    save_profile(base, EnvProfile(name="prod"))
    save_profile(base, EnvProfile(name="dev"))
    assert list_profiles(base) == ["dev", "prod"]


def test_delete_profile(base):
    save_profile(base, EnvProfile(name="temp"))
    delete_profile(base, "temp")
    assert "temp" not in list_profiles(base)


def test_delete_missing_profile_raises(base):
    with pytest.raises(FileNotFoundError):
        delete_profile(base, "ghost")


def test_apply_profile_substitutes_url(base):
    profile = EnvProfile(name="prod", variables={"HOST": "api.example.com"})
    url, headers = apply_profile("https://{{HOST}}/v1", {}, profile)
    assert url == "https://api.example.com/v1"


def test_apply_profile_substitutes_headers(base):
    profile = EnvProfile(name="prod", variables={"TOKEN": "secret"})
    url, headers = apply_profile("https://example.com", {"Authorization": "Bearer {{TOKEN}}"}, profile)
    assert headers["Authorization"] == "Bearer secret"


def test_apply_profile_unknown_placeholder_unchanged(base):
    profile = EnvProfile(name="prod", variables={})
    url, headers = apply_profile("https://{{HOST}}/path", {}, profile)
    assert url == "https://{{HOST}}/path"


def test_profile_get_returns_default(base):
    profile = EnvProfile(name="dev", variables={"A": "1"})
    assert profile.get("A") == "1"
    assert profile.get("MISSING", "default") == "default"
