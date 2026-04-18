"""CLI commands for request rate analysis."""
from __future__ import annotations

import click

from req_replay.storage import RequestStore
from req_replay.rate import analyze_rate


@click.group("rate")
def rate_group() -> None:
    """Analyse request rates over time."""


@rate_group.command("analyze")
@click.option("--store", "store_path", required=True, help="Path to request store directory.")
@click.option("--window", default=60, show_default=True, help="Window size in seconds.")
@click.option("--method", default=None, help="Filter by HTTP method.")
@click.option("--min-count", default=None, type=int, help="Only show windows with at least this many requests.")
def analyze_cmd(store_path: str, window: int, method: str | None, min_count: int | None) -> None:
    """Print per-window request rates."""
    store = RequestStore(store_path)
    requests = store.list()

    if method:
        requests = [r for r in requests if r.method.upper() == method.upper()]

    if not requests:
        click.echo("No requests found.")
        return

    windows = analyze_rate(requests, window_seconds=window)

    if min_count is not None:
        windows = [w for w in windows if w.count >= min_count]

    click.echo(f"Analysed {len(requests)} request(s) across {len(windows)} window(s) ({window}s each)\n")
    for w in windows:
        click.echo(w.summary())
        for m, cnt in sorted(w.methods.items()):
            click.echo(f"  {m}: {cnt}")
