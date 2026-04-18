"""CLI commands for content-type analysis."""
from __future__ import annotations

import click

from req_replay.content_type import analyze_content_types
from req_replay.storage import RequestStore


@click.group("content-type")
def content_type_group() -> None:
    """Analyse Content-Type header distribution."""


@content_type_group.command("analyze")
@click.option("--store", "store_path", required=True, help="Path to request store.")
@click.option("--method", default=None, help="Filter by HTTP method.")
def analyze_cmd(store_path: str, method: str | None) -> None:
    """Show Content-Type distribution for stored requests."""
    store = RequestStore(store_path)
    all_ids = store.list()
    pairs = []
    for rid in all_ids:
        try:
            req, resp = store.load(rid)
        except Exception:
            continue
        if resp is None:
            continue
        if method and req.method.upper() != method.upper():
            continue
        pairs.append((req, resp))

    if not pairs:
        click.echo("No requests found.")
        return

    stats = analyze_content_types(pairs)
    click.echo(stats.display())


@content_type_group.command("top")
@click.option("--store", "store_path", required=True, help="Path to request store.")
@click.option("--n", default=5, show_default=True, help="Number of top types to show.")
def top_cmd(store_path: str, n: int) -> None:
    """Show top N Content-Types across requests and responses."""
    store = RequestStore(store_path)
    pairs = []
    for rid in store.list():
        try:
            req, resp = store.load(rid)
        except Exception:
            continue
        if resp is None:
            continue
        pairs.append((req, resp))

    if not pairs:
        click.echo("No requests found.")
        return

    stats = analyze_content_types(pairs)
    click.echo(f"Top {n} Request Content-Types:")
    for ct, count in stats.top_request_types(n):
        click.echo(f"  {ct}: {count}")
    click.echo(f"Top {n} Response Content-Types:")
    for ct, count in stats.top_response_types(n):
        click.echo(f"  {ct}: {count}")
