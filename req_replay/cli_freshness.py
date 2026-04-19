"""CLI commands for freshness analysis."""
from __future__ import annotations
import click
from req_replay.storage import RequestStore
from req_replay.freshness import analyze_freshness


@click.group("freshness")
def freshness_group() -> None:
    """Analyse response freshness."""


@freshness_group.command("check")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_store", show_default=True)
def check_cmd(request_id: str, store_path: str) -> None:
    """Check freshness for a stored request's response snapshot."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    resp_raw = req.metadata.get("last_response")
    if resp_raw is None:
        click.echo("No response recorded for this request.", err=True)
        raise SystemExit(1)

    from req_replay.models import CapturedResponse
    resp = CapturedResponse.from_dict(resp_raw)
    result = analyze_freshness(request_id, resp)
    click.echo(result.display())


@freshness_group.command("scan")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option("--stale-only", is_flag=True, default=False)
def scan_cmd(store_path: str, stale_only: bool) -> None:
    """Scan all stored requests and report freshness."""
    store = RequestStore(store_path)
    requests = store.list_all()
    if not requests:
        click.echo("No requests found.")
        return

    from req_replay.models import CapturedResponse
    shown = 0
    for req in requests:
        resp_raw = req.metadata.get("last_response")
        if resp_raw is None:
            continue
        resp = CapturedResponse.from_dict(resp_raw)
        result = analyze_freshness(req.id, resp)
        if stale_only and not result.stale:
            continue
        click.echo(result.display())
        click.echo("")
        shown += 1

    if shown == 0:
        click.echo("No matching results.")
