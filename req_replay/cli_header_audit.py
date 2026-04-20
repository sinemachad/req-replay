"""CLI commands for header audit."""
from __future__ import annotations

import click

from req_replay.header_audit import audit_all, audit_headers
from req_replay.storage import RequestStore


@click.group("header-audit")
def header_audit_group() -> None:
    """Audit header hygiene for captured requests."""


@header_audit_group.command("check")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
def check_cmd(request_id: str, store_path: str) -> None:
    """Audit headers for a single request."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    result = audit_headers(req)
    click.echo(result.summary)
    for w in result.warnings:
        click.echo(f"  [{w.code}] {w.header or '-'}: {w.message}")


@header_audit_group.command("scan")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
@click.option("--only-failures", is_flag=True, default=False, help="Only show requests with warnings.")
def scan_cmd(store_path: str, only_failures: bool) -> None:
    """Audit headers for all stored requests."""
    store = RequestStore(store_path)
    requests = store.list_all()

    if not requests:
        click.echo("No requests found.")
        return

    results = audit_all(requests)
    for result in results:
        if only_failures and result.passed:
            continue
        click.echo(result.summary)
        for w in result.warnings:
            click.echo(f"  [{w.code}] {w.header or '-'}: {w.message}")
