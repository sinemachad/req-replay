"""Simple plugin loader for req-replay.

Plugins are plain Python modules placed in a directory.  Each module may
expose any of the following callables:

    on_capture(request, response)  – called after a request is captured
    on_replay(request, result)     – called after a request is replayed
    on_startup()                   – called when the CLI starts
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Callable, List, Optional


@dataclass
class PluginManifest:
    name: str
    path: Path
    module: ModuleType
    on_capture: Optional[Callable] = None
    on_replay: Optional[Callable] = None
    on_startup: Optional[Callable] = None


def _load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load plugin from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def load_plugins(directory: Path) -> List[PluginManifest]:
    """Load all *.py files in *directory* as plugins."""
    manifests: List[PluginManifest] = []
    if not directory.is_dir():
        return manifests
    for py_file in sorted(directory.glob("*.py")):
        mod = _load_module(py_file)
        manifests.append(
            PluginManifest(
                name=py_file.stem,
                path=py_file,
                module=mod,
                on_capture=getattr(mod, "on_capture", None),
                on_replay=getattr(mod, "on_replay", None),
                on_startup=getattr(mod, "on_startup", None),
            )
        )
    return manifests


def run_on_capture(plugins: List[PluginManifest], request, response) -> None:
    for p in plugins:
        if p.on_capture:
            p.on_capture(request, response)


def run_on_replay(plugins: List[PluginManifest], request, result) -> None:
    for p in plugins:
        if p.on_replay:
            p.on_replay(request, result)


def run_on_startup(plugins: List[PluginManifest]) -> None:
    for p in plugins:
        if p.on_startup:
            p.on_startup()
