"""CLI commands for managing plugins."""

from __future__ import annotations

from pathlib import Path

import click

from req_replay.plugin import load_plugins

DEFAULT_PLUGIN_DIR = Path("plugins")


@click.group("plugin")
def plugin_group() -> None:
    """Manage req-replay plugins."""


@plugin_group.command("list")
@click.option(
    "--dir",
    "plugin_dir",
    default=str(DEFAULT_PLUGIN_DIR),
    show_default=True,
    help="Directory to scan for plugins.",
)
def list_cmd(plugin_dir: str) -> None:
    """List all discovered plugins."""
    path = Path(plugin_dir)
    plugins = load_plugins(path)
    if not plugins:
        click.echo(f"No plugins found in '{plugin_dir}'.")
        return
    click.echo(f"Found {len(plugins)} plugin(s) in '{plugin_dir}':\n")
    for p in plugins:
        hooks = ", ".join(
            h
            for h, fn in [
                ("on_capture", p.on_capture),
                ("on_replay", p.on_replay),
                ("on_startup", p.on_startup),
            ]
            if fn is not None
        ) or "(no hooks)"
        click.echo(f"  {p.name}  [{hooks}]")


@plugin_group.command("run-startup")
@click.option(
    "--dir",
    "plugin_dir",
    default=str(DEFAULT_PLUGIN_DIR),
    show_default=True,
    help="Directory to scan for plugins.",
)
def run_startup_cmd(plugin_dir: str) -> None:
    """Execute on_startup hook for all plugins."""
    from req_replay.plugin import run_on_startup

    path = Path(plugin_dir)
    plugins = load_plugins(path)
    run_on_startup(plugins)
    click.echo(f"on_startup executed for {len(plugins)} plugin(s).")
