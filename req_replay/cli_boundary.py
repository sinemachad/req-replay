"""CLI commands for boundary analysis."""
from __future__ import annotations

import click

from req_replay.storage import RequestStore
from req_replay.boundary import analyze_boundaries


@click.group("boundary")
def boundary_group() -> None:
    """Detect requests that cross environment boundaries."""


@boundary_group.command("scan")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
@click.option("--method", default=None, help="Filter by HTTP method")
def scan_cmd(store_path: str, method: str | None) -> None:
    """Scan all stored requests for boundary issues."""
    store = RequestStore(store_path)
    requests = store.list()
    if method:
        requests = [r for r in requests if (r.method or "").upper() == method.upper()]
    if not requests:
        click.echo("No requests found.")
        return
    result = analyze_boundaries(requests)
    click.echo(result.display())


@boundary_group.command("check")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
def check_cmd(request_id: str, store_path: str) -> None:
    """Check a single request for boundary issues."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)
    result = analyze_boundaries([req])
    click.echo(result.display())
    if not result.passed():
        raise SystemExit(1)
