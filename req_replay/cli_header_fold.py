"""CLI commands for header fold analysis."""
from __future__ import annotations

import click

from req_replay.header_fold import analyze_header_fold
from req_replay.storage import RequestStore


@click.group("header-fold")
def header_fold_group() -> None:
    """Detect and report obs-fold (multi-line) header values."""


@header_fold_group.command("check")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_store", show_default=True)
def check_cmd(request_id: str, store_path: str) -> None:
    """Check a single request for obs-fold header values."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Error: request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    result = analyze_header_fold(req)
    click.echo(result.summary())
    if not result.passed:
        for w in result.warnings:
            click.echo(f"  [{w.code}] {w.header}: {w.original_value!r}")


@header_fold_group.command("scan")
@click.option("--store", "store_path", default=".req_store", show_default=True)
def scan_cmd(store_path: str) -> None:
    """Scan all stored requests for obs-fold header values."""
    store = RequestStore(store_path)
    ids = store.list_ids()
    if not ids:
        click.echo("No requests found.")
        return

    total_warnings = 0
    for rid in ids:
        req = store.load(rid)
        result = analyze_header_fold(req)
        if not result.passed:
            click.echo(f"{rid}: {result.summary()}")
            for w in result.warnings:
                click.echo(f"  [{w.code}] {w.header}")
            total_warnings += len(result.warnings)

    if total_warnings == 0:
        click.echo("All requests OK – no obs-fold headers detected.")
    else:
        click.echo(f"\nTotal warnings: {total_warnings}")
