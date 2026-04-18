"""CLI commands for deprecation header analysis."""
from __future__ import annotations

import click

from req_replay.storage import RequestStore
from req_replay.snapshot import load_snapshot
from req_replay.deprecation import check_deprecations


@click.group("deprecation")
def deprecation_group() -> None:
    """Detect deprecated HTTP headers in stored requests/responses."""


@deprecation_group.command("check")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
@click.option("--snapshot", "snapshot_name", default=None, help="Snapshot name to check response headers.")
def check_cmd(request_id: str, store_path: str, snapshot_name: str | None) -> None:
    """Check a captured request (and optional snapshot response) for deprecated headers."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    response = None
    if snapshot_name:
        try:
            response = load_snapshot(store_path, request_id, snapshot_name)
        except FileNotFoundError:
            click.echo(f"Snapshot '{snapshot_name}' not found for request '{request_id}'.", err=True)
            raise SystemExit(1)

    result = check_deprecations(req, response)
    click.echo(result.summary())
    if not result.passed:
        raise SystemExit(1)


@deprecation_group.command("scan")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
def scan_cmd(store_path: str) -> None:
    """Scan all stored requests for deprecated request headers."""
    store = RequestStore(store_path)
    ids = store.list_ids()
    if not ids:
        click.echo("No requests stored.")
        return

    total_warnings = 0
    for rid in ids:
        req = store.load(rid)
        result = check_deprecations(req)
        if not result.passed:
            click.echo(f"[{rid}] {req.method} {req.url}")
            for w in result.warnings:
                click.echo(f"  [{w.source}] {w.header}: {w.reason}")
            total_warnings += len(result.warnings)

    if total_warnings == 0:
        click.echo("All requests clean — no deprecated headers found.")
    else:
        click.echo(f"\n{total_warnings} deprecated header(s) found across {len(ids)} request(s).")
