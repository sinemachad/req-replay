"""CLI commands for quota analysis."""
from __future__ import annotations

import click

from req_replay.quota import analyze_quota
from req_replay.storage import RequestStore


@click.group("quota")
def quota_group() -> None:
    """Analyse request replay quotas."""


@quota_group.command("analyze")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
@click.option("--limit", default=100, show_default=True, help="Max allowed replays per request ID.")
def analyze_cmd(store_path: str, limit: int) -> None:
    """Show quota usage for all stored requests."""
    store = RequestStore(store_path)
    requests = store.list()
    if not requests:
        click.echo("No requests found.")
        return
    results = analyze_quota(requests, limit=limit)
    for result in results:
        status = click.style("PASS", fg="green") if result.passed() else click.style("WARN", fg="yellow")
        click.echo(f"[{status}] {result.summary()}")
        for w in result.warnings:
            click.echo(f"       {w.code}: {w.message}")


@quota_group.command("check")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
@click.option("--limit", default=100, show_default=True)
def check_cmd(request_id: str, store_path: str, limit: int) -> None:
    """Check quota for a single request ID."""
    store = RequestStore(store_path)
    all_requests = store.list()
    matching = [r for r in all_requests if r.id == request_id]
    if not matching:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)
    results = analyze_quota(matching, limit=limit)
    for result in results:
        status = click.style("PASS", fg="green") if result.passed() else click.style("WARN", fg="yellow")
        click.echo(f"[{status}] {result.summary()}")
        for w in result.warnings:
            click.echo(f"  {w.code}: {w.message}")
