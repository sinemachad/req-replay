"""CLI commands for header diff."""
from __future__ import annotations

import click

from req_replay.header_diff import diff_headers
from req_replay.storage import RequestStore


@click.group("header-diff")
def header_diff_group() -> None:
    """Compare headers between two stored requests."""


@header_diff_group.command("compare")
@click.argument("id_a")
@click.argument("id_b")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
@click.option(
    "--ignore",
    multiple=True,
    metavar="HEADER",
    help="Header names to exclude from comparison (repeatable).",
)
def compare_cmd(
    id_a: str,
    id_b: str,
    store_path: str,
    ignore: tuple,
) -> None:
    """Show header differences between request ID_A and ID_B."""
    store = RequestStore(store_path)

    try:
        req_a = store.load(id_a)
    except FileNotFoundError:
        click.echo(f"Error: request '{id_a}' not found.", err=True)
        raise SystemExit(1)

    try:
        req_b = store.load(id_b)
    except FileNotFoundError:
        click.echo(f"Error: request '{id_b}' not found.", err=True)
        raise SystemExit(1)

    result = diff_headers(req_a, req_b, ignore=set(ignore))
    click.echo(result.summary())

    if result.added:
        click.echo("\nAdded (in B):")
        for k, v in sorted(result.added.items()):
            click.echo(f"  + {k}: {v}")

    if result.removed:
        click.echo("\nRemoved (not in B):")
        for k, v in sorted(result.removed.items()):
            click.echo(f"  - {k}: {v}")

    if result.changed:
        click.echo("\nChanged:")
        for k, (va, vb) in sorted(result.changed.items()):
            click.echo(f"  ~ {k}: '{va}' -> '{vb}'")

    if result.warnings:
        click.echo("\nWarnings:")
        for w in result.warnings:
            click.echo(f"  [{w.code}] {w.message}")
