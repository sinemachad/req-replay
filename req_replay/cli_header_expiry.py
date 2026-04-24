"""CLI commands for header expiry analysis."""
from __future__ import annotations

import click

from req_replay.header_expiry import analyze_expiry
from req_replay.storage import RequestStore


@click.group("header-expiry")
def header_expiry_group() -> None:
    """Inspect expiry-related response/request headers."""


@header_expiry_group.command("check")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_store", show_default=True)
def check_cmd(request_id: str, store_path: str) -> None:
    """Check expiry headers for a single captured request."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Error: request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    result = analyze_expiry(req)
    click.echo(result.display())
    if not result.passed():
        raise SystemExit(1)


@header_expiry_group.command("scan")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option("--fail-fast", is_flag=True, default=False)
def scan_cmd(store_path: str, fail_fast: bool) -> None:
    """Scan all stored requests for expired headers."""
    store = RequestStore(store_path)
    requests = store.list()
    if not requests:
        click.echo("No requests found.")
        return

    any_failed = False
    for req_id in requests:
        req = store.load(req_id)
        result = analyze_expiry(req)
        click.echo(result.summary())
        if not result.passed():
            any_failed = True
            if fail_fast:
                raise SystemExit(1)

    if any_failed:
        raise SystemExit(1)
