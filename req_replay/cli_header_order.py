"""CLI commands for header-order analysis."""
from __future__ import annotations

import click

from req_replay.storage import RequestStore
from req_replay.header_order import analyze_header_order, summarize_header_orders


@click.group("header-order")
def header_order_group() -> None:
    """Inspect and summarise HTTP header ordering."""


@header_order_group.command("check")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
def check_cmd(request_id: str, store_path: str) -> None:
    """Show header ordering for a single captured request."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Error: request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    result = analyze_header_order(req)
    click.echo(result.display())


@header_order_group.command("scan")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
@click.option(
    "--non-canonical-only",
    is_flag=True,
    default=False,
    help="Print only requests with non-canonical header ordering.",
)
def scan_cmd(store_path: str, non_canonical_only: bool) -> None:
    """Scan all stored requests and report header ordering."""
    store = RequestStore(store_path)
    requests = store.list_all()

    if not requests:
        click.echo("No requests found.")
        return

    stats = summarize_header_orders(requests)
    click.echo(stats.display())
    click.echo()

    for req in requests:
        result = analyze_header_order(req)
        if non_canonical_only and result.is_canonical:
            continue
        status = "✓" if result.is_canonical else "✗"
        click.echo(f"  [{status}] {req.id}  {', '.join(result.ordered_keys)}")
