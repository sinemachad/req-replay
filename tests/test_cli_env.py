"""Tests for req_replay.cli_env."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from req_replay.cli_env import env_group
from req_replay.env import save_profile, load_profile, EnvProfile


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def store_path(tmp_path):
    return str(tmp_path)


def test_set_creates_profile(runner, store_path):
    result = runner.invoke(env_group, ["set", "dev", "HOST", "localhost", "--store-dir", store_path])
    assert result.exit_code == 0
    assert "Set HOST=localhost" in result.output
    profile = load_profile(Path(store_path), "dev")
    assert profile.variables["HOST"] == "localhost"


def test_set_updates_existing_profile(runner, store_path):
    save_profile(Path(store_path), EnvProfile(name="dev", variables={"A": "1"}))
    runner.invoke(env_group, ["set", "dev", "B", "2", "--store-dir", store_path])
    profile = load_profile(Path(store_path), "dev")
    assert profile.variables["A"] == "1"
    assert profile.variables["B"] == "2"


def test_show_profile(runner, store_path):
    save_profile(Path(store_path), EnvProfile(name="prod", variables={"KEY": "val"}))
    result = runner.invoke(env_group, ["show", "prod", "--store-dir", store_path])
    assert result.exit_code == 0
    assert "KEY" in result.output
    assert "val" in result.output


def test_show_missing_profile(runner, store_path):
    result = runner.invoke(env_group, ["show", "missing", "--store-dir", store_path])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_list_profiles(runner, store_path):
    save_profile(Path(store_path), EnvProfile(name="alpha"))
    save_profile(Path(store_path), EnvProfile(name="beta"))
    result = runner.invoke(env_group, ["list", "--store-dir", store_path])
    assert "alpha" in result.output
    assert "beta" in result.output


def test_list_empty(runner, store_path):
    result = runner.invoke(env_group, ["list", "--store-dir", store_path])
    assert "No profiles" in result.output


def test_delete_profile(runner, store_path):
    save_profile(Path(store_path), EnvProfile(name="tmp"))
    result = runner.invoke(env_group, ["delete", "tmp", "--store-dir", store_path])
    assert result.exit_code == 0
    assert "Deleted" in result.output


def test_delete_missing_profile(runner, store_path):
    result = runner.invoke(env_group, ["delete", "ghost", "--store-dir", store_path])
    assert result.exit_code != 0
