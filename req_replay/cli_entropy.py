"""CLI commands for entropy analysis."""
from __future__ import annotations
import click
from req_replay.storage import RequestStore
from req_replay.entropy import analyze_entropy, DEFAULT_THRESHOLD


@click.group("entropy")
def entropy_group() -> None:
    """Detect high-entropy (potentially secret) values in requests."""


@entropy_group.command("check")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
@click.option("--threshold", default=DEFAULT_THRESHOLD, show_default=True, type=float)
def check_cmd(request_id: str, store_path: str, threshold: float) -> None:
    """Check a single request for high-entropy values."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)
    result = analyze_entropy(req, threshold=threshold)
    click.echo(result.summary())


@entropy_group.command("scan")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
@click.option("--threshold", default=DEFAULT_THRESHOLD, show_default=True, type=float)
def scan_cmd(store_path: str, threshold: float) -> None:
    """Scan all stored requests for high-entropy values."""
    store = RequestStore(store_path)
    ids = store.list_ids()
    if not ids:
        click.echo("No requests stored.")
        return
    flagged = 0
    for rid in ids:
        req = store.load(rid)
        result = analyze_entropy(req, threshold=threshold)
        if not result.passed():
            flagged += 1
            click.echo(f"[{rid}] {req.method} {req.url}")
            for h in result.hits:
                click.echo(f"  {h.location}  entropy={h.entropy:.2f}")
    if flagged == 0:
        click.echo("All requests clean.")
    else:
        click.echo(f"\n{flagged} request(s) with high-entropy values.")
