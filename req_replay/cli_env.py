"""CLI commands for environment profile management."""
from __future__ import annotations

import json
from pathlib import Path

import click

from req_replay.env import EnvProfile, save_profile, load_profile, list_profiles, delete_profile


@click.group("env")
def env_group() -> None:
    """Manage environment variable profiles."""


@env_group.command("set")
@click.argument("name")
@click.argument("key")
@click.argument("value")
@click.option("--store-dir", default=".req_replay", show_default=True)
def set_var(name: str, key: str, value: str, store_dir: str) -> None:
    """Set a variable in an environment profile."""
    base = Path(store_dir)
    try:
        profile = load_profile(base, name)
    except FileNotFoundError:
        profile = EnvProfile(name=name)
    profile.variables[key] = value
    save_profile(base, profile)
    click.echo(f"Set {key}={value} in profile '{name}'.")


@env_group.command("show")
@click.argument("name")
@click.option("--store-dir", default=".req_replay", show_default=True)
def show_profile(name: str, store_dir: str) -> None:
    """Show variables in an environment profile."""
    try:
        profile = load_profile(Path(store_dir), name)
    except FileNotFoundError:
        click.echo(f"Profile '{name}' not found.", err=True)
        raise click.Abort()
    click.echo(json.dumps(profile.variables, indent=2))


@env_group.command("list")
@click.option("--store-dir", default=".req_replay", show_default=True)
def list_cmd(store_dir: str) -> None:
    """List available environment profiles."""
    profiles = list_profiles(Path(store_dir))
    if not profiles:
        click.echo("No profiles found.")
    for p in profiles:
        click.echo(p)


@env_group.command("delete")
@click.argument("name")
@click.option("--store-dir", default=".req_replay", show_default=True)
def delete_cmd(name: str, store_dir: str) -> None:
    """Delete an environment profile."""
    try:
        delete_profile(Path(store_dir), name)
        click.echo(f"Deleted profile '{name}'.")
    except FileNotFoundError:
        click.echo(f"Profile '{name}' not found.", err=True)
        raise click.Abort()
