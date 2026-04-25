"""CLI commands for header size analysis."""
from __future__ import annotations

import click

from req_replay.header_size import analyze_header_sizes
from req_replay.storage import RequestStore


@click.group("header-size")
def header_size_group() -> None:
    """Analyse the byte size of request headers."""


@header_size_group.command("analyze")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option("--threshold", default=8192, show_default=True, help="Warn above N bytes")
@click.option("--method", default=None, help="Filter by HTTP method")
def analyze_cmd(store_path: str, threshold: int, method: str | None) -> None:
    """Print header size statistics for all stored requests."""
    store = RequestStore(store_path)
    requests = store.list()
    if method:
        requests = [r for r in requests if r.method.upper() == method.upper()]
    stats = analyze_header_sizes(requests, threshold=threshold)
    click.echo(stats.display())


@header_size_group.command("top")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option("-n", "top_n", default=10, show_default=True, help="Show top N requests")
@click.option("--threshold", default=8192, show_default=True)
def top_cmd(store_path: str, top_n: int, threshold: int) -> None:
    """List the requests with the largest header payloads."""
    store = RequestStore(store_path)
    requests = store.list()
    stats = analyze_header_sizes(requests, threshold=threshold)
    sorted_ids = sorted(stats.by_request, key=lambda i: stats.by_request[i], reverse=True)
    for req_id in sorted_ids[:top_n]:
        size = stats.by_request[req_id]
        flag = " [OVER]" if size > threshold else ""
        click.echo(f"{req_id}  {size} bytes{flag}")
