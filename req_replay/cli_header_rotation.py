"""CLI commands for header rotation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import click

from req_replay.header_rotation import RotationConfig, rotate_headers
from req_replay.storage import RequestStore


@click.group("header-rotation")
def header_rotation_group() -> None:
    """Rotate header values across captured requests."""


def _parse_kv(pairs: tuple[str, ...]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for pair in pairs:
        if "=" not in pair:
            raise click.BadParameter(f"Expected key=value, got {pair!r}")
        k, v = pair.split("=", 1)
        result.setdefault(k.lower(), []).append(v)
    return result


@header_rotation_group.command("apply")
@click.argument("request_id")
@click.option(
    "--store",
    "store_path",
    default=".req_replay",
    show_default=True,
    help="Path to the request store.",
)
@click.option(
    "--header",
    "headers",
    multiple=True,
    metavar="NAME=VALUE",
    help="Header rotation pool entry (repeatable; same name = multiple values).",
)
@click.option("--dry-run", is_flag=True, help="Show changes without saving.")
def apply_cmd(
    request_id: str,
    store_path: str,
    headers: tuple[str, ...],
    dry_run: bool,
) -> None:
    """Apply one round of header rotation to REQUEST_ID."""
    store = RequestStore(Path(store_path))
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Error: request {request_id!r} not found.", err=True)
        raise SystemExit(1)

    pool = _parse_kv(headers)
    if not pool:
        click.echo("No --header options provided; nothing to rotate.")
        return

    config = RotationConfig(values=pool)
    new_req, results = rotate_headers(req, config)

    for r in results:
        click.echo(r.display())

    if not dry_run:
        store.save(new_req)
        click.echo(f"Saved rotated request {request_id}.")
    else:
        click.echo("(dry-run: no changes saved)")
