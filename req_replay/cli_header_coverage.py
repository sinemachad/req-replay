"""CLI commands for header coverage analysis."""
from __future__ import annotations

import click

from req_replay.header_coverage import analyze_header_coverage
from req_replay.storage import RequestStore


@click.group("header-coverage")
def header_coverage_group() -> None:
    """Analyse header coverage across stored requests."""


@header_coverage_group.command("analyze")
@click.option("--store", "store_path", required=True, help="Path to request store.")
@click.option("--top", "top_n", default=0, help="Show only top N headers (0 = all).")
def analyze_cmd(store_path: str, top_n: int) -> None:
    """Print header coverage statistics for all stored requests."""
    store = RequestStore(store_path)
    requests = store.list()
    if not requests:
        click.echo("No requests found.")
        return
    stats = analyze_header_coverage(requests)
    if top_n > 0:
        keys = stats.top(top_n)
        click.echo(f"Top {top_n} headers (out of {len(stats.header_presence)} unique):")
        for k in keys:
            count = stats.header_presence[k]
            pct = stats.header_coverage[k]
            click.echo(f"  {k:<40} {count:>6}  {pct:>7.1f}%")
    else:
        click.echo(stats.display())


@header_coverage_group.command("missing")
@click.argument("request_id")
@click.option("--store", "store_path", required=True, help="Path to request store.")
def missing_cmd(request_id: str, store_path: str) -> None:
    """List headers present in the corpus but absent from a specific request."""
    store = RequestStore(store_path)
    try:
        target = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    all_requests = store.list()
    stats = analyze_header_coverage(all_requests)
    missing = stats.missing_from(target)

    if not missing:
        click.echo("No missing headers — request contains all corpus headers.")
    else:
        click.echo(f"Headers missing from {request_id}:")
        for h in sorted(missing):
            pct = stats.header_coverage.get(h, 0.0)
            click.echo(f"  {h:<40}  corpus coverage: {pct:.1f}%")
