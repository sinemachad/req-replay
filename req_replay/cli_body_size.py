"""CLI commands for body-size analysis."""
from __future__ import annotations

import click

from req_replay.body_size import analyze_request_sizes, analyze_response_sizes
from req_replay.storage import RequestStore


@click.group("body-size")
def body_size_group() -> None:
    """Analyse request and response body sizes."""


@body_size_group.command("requests")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option("--method", default=None, help="Filter by HTTP method.")
def requests_cmd(store_path: str, method: str | None) -> None:
    """Show body-size stats for captured requests."""
    store = RequestStore(store_path)
    reqs = store.list()
    if method:
        reqs = [r for r in reqs if r.method.upper() == method.upper()]
    stats = analyze_request_sizes(reqs)
    click.echo(stats.display())


@body_size_group.command("responses")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option("--method", default=None, help="Filter by HTTP method.")
def responses_cmd(store_path: str, method: str | None) -> None:
    """Show body-size stats for captured responses."""
    store = RequestStore(store_path)
    reqs = store.list()
    if method:
        reqs = [r for r in reqs if r.method.upper() == method.upper()]
    pairs = []
    for req in reqs:
        resp = store.load_response(req.id) if hasattr(store, "load_response") else None
        if resp is not None:
            pairs.append((req, resp))
    stats = analyze_response_sizes(pairs)
    click.echo(stats.display())
