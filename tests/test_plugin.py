"""Tests for req_replay.plugin."""

from __future__ import annotations

from pathlib import Path

import pytest

from req_replay.plugin import (
    load_plugins,
    run_on_capture,
    run_on_replay,
    run_on_startup,
)


def _write_plugin(directory: Path, name: str, source: str) -> Path:
    p = directory / f"{name}.py"
    p.write_text(source)
    return p


def test_load_plugins_empty_dir(tmp_path):
    plugins = load_plugins(tmp_path)
    assert plugins == []


def test_load_plugins_missing_dir(tmp_path):
    plugins = load_plugins(tmp_path / "nonexistent")
    assert plugins == []


def test_load_plugins_detects_hooks(tmp_path):
    _write_plugin(
        tmp_path,
        "myplugin",
        "def on_capture(req, resp): pass\ndef on_startup(): pass\n",
    )
    plugins = load_plugins(tmp_path)
    assert len(plugins) == 1
    p = plugins[0]
    assert p.name == "myplugin"
    assert p.on_capture is not None
    assert p.on_startup is not None
    assert p.on_replay is None


def test_load_plugins_no_hooks(tmp_path):
    _write_plugin(tmp_path, "empty", "# nothing\n")
    plugins = load_plugins(tmp_path)
    assert len(plugins) == 1
    assert plugins[0].on_capture is None
    assert plugins[0].on_replay is None
    assert plugins[0].on_startup is None


def test_run_on_startup_calls_hook(tmp_path):
    _write_plugin(
        tmp_path,
        "startup_plugin",
        "called = []\ndef on_startup():\n    called.append(1)\n",
    )
    plugins = load_plugins(tmp_path)
    run_on_startup(plugins)
    assert plugins[0].module.called == [1]


def test_run_on_capture_calls_hook(tmp_path):
    _write_plugin(
        tmp_path,
        "cap_plugin",
        "calls = []\ndef on_capture(req, resp):\n    calls.append((req, resp))\n",
    )
    plugins = load_plugins(tmp_path)
    run_on_capture(plugins, "REQ", "RESP")
    assert plugins[0].module.calls == [("REQ", "RESP")]


def test_run_on_replay_calls_hook(tmp_path):
    _write_plugin(
        tmp_path,
        "replay_plugin",
        "calls = []\ndef on_replay(req, result):\n    calls.append((req, result))\n",
    )
    plugins = load_plugins(tmp_path)
    run_on_replay(plugins, "REQ", "RESULT")
    assert plugins[0].module.calls == [("REQ", "RESULT")]


def test_multiple_plugins_all_called(tmp_path):
    for i in range(3):
        _write_plugin(
            tmp_path,
            f"plugin_{i}",
            f"calls = []\ndef on_startup():\n    calls.append({i})\n",
        )
    plugins = load_plugins(tmp_path)
    assert len(plugins) == 3
    run_on_startup(plugins)
    for p in plugins:
        assert len(p.module.calls) == 1
