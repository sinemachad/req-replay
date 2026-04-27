"""CLI commands for detecting deprecated HTTP headers."""
from __future__ import annotations

import click

from req_replay.header_deprecation import check_deprecated_headers, scan_deprecated_headers
from req_replay.storage import RequestStore


@click.group("header-deprecation")
def header_deprecation_group() -> None:
    """Detect deprecated or legacy HTTP headers."""


@header_deprecation_group.command("check")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_store", show_default=True)
def check_cmd(request_id: str, store_path: str) -> None:
    """Check a single request for deprecated headers."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Error: request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    result = check_deprecated_headers(req)
    click.echo(result.display())
    if not result.passed:
        raise SystemExit(1)


@header_deprecation_group.command("scan")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option("--only-warn", is_flag=True, default=False, help="Only show requests with warnings")
def scan_cmd(store_path: str, only_warn: bool) -> None:
    """Scan all stored requests for deprecated headers."""
    store = RequestStore(store_path)
    requests = store.list_all()

    if not requests:
        click.echo("No requests found in store.")
        return

    results = scan_deprecated_headers(requests)
    any_warn = False
    for result in results:
        if only_warn and result.passed:
            continue
        rid = result.request_id or "unknown"
        status = "PASS" if result.passed else "WARN"
        click.echo(f"[{status}] {rid}: {result.summary()}")
        if not result.passed:
            any_warn = True
            for w in result.warnings:
                click.echo(f"       [{w.code}] {w.header} — {w.suggestion}")

    if any_warn:
        raise SystemExit(1)
