"""CLI commands for CORS analysis."""
from __future__ import annotations
import click
from req_replay.storage import RequestStore
from req_replay.snapshot import load_snapshot
from req_replay.cors import analyze_cors


@click.group("cors")
def cors_group() -> None:
    """Analyse CORS headers for captured requests."""


@cors_group.command("check")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_store", show_default=True)
def check_cmd(request_id: str, store_path: str) -> None:
    """Check CORS headers for a single captured request/response pair."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    try:
        resp = load_snapshot(store_path, request_id)
    except FileNotFoundError:
        click.echo(f"No snapshot found for '{request_id}'. Capture a response first.", err=True)
        raise SystemExit(1)

    info = analyze_cors(req, resp)
    click.echo(info.display())
    if not info.passed():
        raise SystemExit(2)


@cors_group.command("scan")
@click.option("--store", "store_path", default=".req_store", show_default=True)
def scan_cmd(store_path: str) -> None:
    """Scan all stored requests for CORS issues."""
    store = RequestStore(store_path)
    ids = store.list_ids()
    if not ids:
        click.echo("No requests stored.")
        return

    issues = 0
    for rid in ids:
        req = store.load(rid)
        try:
            resp = load_snapshot(store_path, rid)
        except FileNotFoundError:
            continue
        info = analyze_cors(req, resp)
        if not info.passed():
            click.echo(f"[{rid}] {len(info.warnings)} warning(s):")
            for w in info.warnings:
                click.echo(f"  ! {w}")
            issues += 1

    if issues == 0:
        click.echo("No CORS issues found.")
    else:
        click.echo(f"\n{issues} request(s) with CORS issues.")
