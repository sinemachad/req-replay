"""Tests for req_replay.cli_group CLI commands."""
import pytest
from click.testing import CliRunner

from req_replay.cli_group import group_cmd
from req_replay.models import CapturedRequest
from req_replay.storage import RequestStore


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def store_path(tmp_path):
    return str(tmp_path / "store")


def _invoke(runner, args, store_path):
    return runner.invoke(group_cmd, args + ["--store-path", store_path])


def test_create_outputs_name(runner, store_path):
    result = _invoke(runner, ["create", "smoke"], store_path)
    assert result.exit_code == 0
    assert "smoke" in result.output


def test_create_with_description(runner, store_path):
    result = _invoke(runner, ["create", "smoke", "-d", "regression"], store_path)
    assert result.exit_code == 0


def test_add_to_existing_group(runner, store_path):
    _invoke(runner, ["create", "g1"], store_path)
    result = _invoke(runner, ["add", "g1", "req-abc"], store_path)
    assert result.exit_code == 0
    assert "req-abc" in result.output


def test_add_to_missing_group_exits_1(runner, store_path):
    result = _invoke(runner, ["add", "ghost", "req-abc"], store_path)
    assert result.exit_code == 1


def test_remove_from_group(runner, store_path):
    _invoke(runner, ["create", "g1"], store_path)
    _invoke(runner, ["add", "g1", "req-abc"], store_path)
    result = _invoke(runner, ["remove", "g1", "req-abc"], store_path)
    assert result.exit_code == 0
    assert "req-abc" in result.output


def test_list_empty(runner, store_path):
    result = _invoke(runner, ["list"], store_path)
    assert result.exit_code == 0
    assert "No groups" in result.output


def test_list_shows_names(runner, store_path):
    _invoke(runner, ["create", "alpha"], store_path)
    _invoke(runner, ["create", "beta"], store_path)
    result = _invoke(runner, ["list"], store_path)
    assert "alpha" in result.output
    assert "beta" in result.output


def test_show_group(runner, store_path):
    _invoke(runner, ["create", "g1", "-d", "my group"], store_path)
    _invoke(runner, ["add", "g1", "r1"], store_path)
    result = _invoke(runner, ["show", "g1"], store_path)
    assert result.exit_code == 0
    assert "g1" in result.output
    assert "r1" in result.output


def test_show_missing_group_exits_1(runner, store_path):
    result = _invoke(runner, ["show", "nope"], store_path)
    assert result.exit_code == 1
