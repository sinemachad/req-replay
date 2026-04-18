"""CLI commands for HTTP protocol version analysis."""
from __future__ import annotations

import click

from req_replay.protocol import analyze_protocols
from req_replay.storage import RequestStore


@click.group("protocol")
def protocol_group() -> None:
    """Analyse HTTP protocol versions used in captured requests."""


@protocol_group.command("analyze")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
@click.option("--method", default=None, help="Filter by HTTP method.")
def analyze_cmd(store_path: str, method: str | None) -> None:
    """Print a breakdown of HTTP protocol versions."""
    store = RequestStore(store_path)
    requests = store.list()
    if method:
        requests = [r for r in requests if r.method.upper() == method.upper()]
    stats = analyze_protocols(requests)
    click.echo(stats.display())


@protocol_group.command("top")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
@click.option("--n", default=3, show_default=True, help="Number of top versions to show.")
def top_cmd(store_path: str, n: int) -> None:
    """Show the top N most-used protocol versions."""
    store = RequestStore(store_path)
    requests = store.list()
    stats = analyze_protocols(requests)
    if stats.total == 0:
        click.echo("No requests found.")
        return
    sorted_versions = sorted(
        stats.version_counts.items(), key=lambda x: x[1], reverse=True
    )
    click.echo(f"Top {n} protocol versions:")
    for version, count in sorted_versions[:n]:
        click.echo(f"  {version}: {count}")
