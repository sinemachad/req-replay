"""CLI commands for header frequency analysis."""
from __future__ import annotations

import click

from req_replay.storage import RequestStore
from req_replay.header_freq import analyze_header_freq


@click.group("header-freq")
def header_freq_group() -> None:
    """Analyse header name/value frequency across stored requests."""


@header_freq_group.command("analyze")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option("--top", default=10, show_default=True, help="Number of headers to show.")
def analyze_cmd(store_path: str, top: int) -> None:
    """Show the most common headers across all stored requests."""
    store = RequestStore(store_path)
    requests = [store.load(rid) for rid in store.list_ids()]
    if not requests:
        click.echo("No requests found.")
        return
    stats = analyze_header_freq(requests)
    click.echo(f"Total requests: {stats.total_requests}")
    click.echo(f"Top {top} headers:")
    for name, count in stats.top_headers(top):
        pct = 100.0 * stats.coverage(name)
        click.echo(f"  {name}: {count} ({pct:.1f}% of requests)")


@header_freq_group.command("values")
@click.argument("header_name")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option("--top", default=5, show_default=True, help="Number of values to show.")
def values_cmd(header_name: str, store_path: str, top: int) -> None:
    """Show the most common values for a specific header."""
    store = RequestStore(store_path)
    requests = [store.load(rid) for rid in store.list_ids()]
    if not requests:
        click.echo("No requests found.")
        return
    stats = analyze_header_freq(requests)
    top_vals = stats.top_values(header_name, top)
    if not top_vals:
        click.echo(f"No data for header '{header_name}'.")
        return
    click.echo(f"Top values for '{header_name}':")
    for val, count in top_vals:
        click.echo(f"  {val!r}: {count}")
