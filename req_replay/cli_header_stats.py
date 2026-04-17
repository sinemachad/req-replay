"""CLI commands for header statistics."""
from __future__ import annotations

import click

from req_replay.storage import RequestStore
from req_replay.header_stats import analyze_headers


@click.group("header-stats")
def header_stats_group() -> None:
    """Analyse header usage across stored requests."""


@header_stats_group.command("show")
@click.option("--store", "store_path", required=True, type=click.Path(), help="Path to request store directory.")
@click.option("--top", default=0, help="Limit output to top N headers (0 = all).")
def show_cmd(store_path: str, top: int) -> None:
    """Print header frequency table for all stored requests."""
    store = RequestStore(store_path)
    requests = [store.load(rid) for rid in store.list_ids()]
    if not requests:
        click.echo("No requests found.")
        return
    stats = analyze_headers(requests)
    if top:
        limited = dict(
            sorted(stats.header_frequency.items(), key=lambda x: -x[1])[:top]
        )
        stats.header_frequency = limited
    click.echo(stats.display())


@header_stats_group.command("values")
@click.argument("header_name")
@click.option("--store", "store_path", required=True, type=click.Path(), help="Path to request store directory.")
def values_cmd(header_name: str, store_path: str) -> None:
    """Show value distribution for a specific header."""
    store = RequestStore(store_path)
    requests = [store.load(rid) for rid in store.list_ids()]
    stats = analyze_headers(requests)
    key = header_name.lower()
    values = stats.value_frequency.get(key)
    if not values:
        click.echo(f"Header '{header_name}' not found in any request.")
        return
    click.echo(f"Values for '{key}':")
    for val, cnt in sorted(values.items(), key=lambda x: -x[1]):
        click.echo(f"  {val!r:50s} {cnt}")
