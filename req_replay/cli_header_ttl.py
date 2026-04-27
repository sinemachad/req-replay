"""CLI commands for TTL header analysis."""
from __future__ import annotations

import click

from req_replay.header_ttl import analyze_ttl, extract_ttl
from req_replay.storage import RequestStore


@click.group("header-ttl")
def header_ttl_group() -> None:
    """Analyse TTL hints in response headers."""


@header_ttl_group.command("check")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_store", show_default=True)
def check_cmd(request_id: str, store_path: str) -> None:
    """Show TTL hint for a single stored request/response pair."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request {request_id!r} not found.", err=True)
        raise SystemExit(1)

    resp = getattr(req, "response", None)
    if resp is None:
        click.echo("No response stored for this request.", err=True)
        raise SystemExit(1)

    ttl, source = extract_ttl(resp)
    if ttl is None:
        click.echo("No TTL hint found in response headers.")
    else:
        click.echo(f"TTL: {ttl}s  (source: {source})")


@header_ttl_group.command("scan")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option("--no-ttl-only", is_flag=True, default=False,
              help="Only show responses without a TTL hint.")
def scan_cmd(store_path: str, no_ttl_only: bool) -> None:
    """Scan all stored responses and report TTL hints."""
    store = RequestStore(store_path)
    requests = store.list_all()

    pairs = []
    for req in requests:
        resp = getattr(req, "response", None)
        if resp is not None:
            pairs.append((req, resp))

    if not pairs:
        click.echo("No request/response pairs found.")
        return

    stats = analyze_ttl(pairs)
    click.echo(stats.display())
    click.echo()

    for result in stats.results:
        if no_ttl_only and result.ttl_seconds is not None:
            continue
        click.echo(result.display())
