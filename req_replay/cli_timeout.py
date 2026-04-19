"""CLI commands for timeout analysis."""
from __future__ import annotations

import click

from req_replay.storage import RequestStore
from req_replay.timeout import analyze_timeouts


@click.group("timeout")
def timeout_group() -> None:
    """Analyse request timeouts."""


@timeout_group.command("analyze")
@click.argument("store_path", type=click.Path())
@click.option(
    "--threshold",
    default=5000.0,
    show_default=True,
    help="Timeout threshold in milliseconds.",
)
@click.option(
    "--method",
    default=None,
    help="Filter by HTTP method.",
)
def analyze_cmd(store_path: str, threshold: float, method: str | None) -> None:
    """Print timeout statistics for all stored requests."""
    store = RequestStore(store_path)
    requests = store.list()

    pairs = []
    for req in requests:
        if method and req.method.upper() != method.upper():
            continue
        resp = req.metadata.get("_response") if req.metadata else None
        # We only need the request for duration analysis; pass a dummy resp.
        from req_replay.models import CapturedResponse
        dummy = CapturedResponse(status_code=0, headers={}, body=None)
        pairs.append((req, dummy))

    stats = analyze_timeouts(pairs, threshold_ms=threshold)
    click.echo(stats.display())


@timeout_group.command("list-slow")
@click.argument("store_path", type=click.Path())
@click.option("--threshold", default=5000.0, show_default=True)
def list_slow_cmd(store_path: str, threshold: float) -> None:
    """List requests that exceeded the timeout threshold."""
    store = RequestStore(store_path)
    requests = store.list()

    found = False
    for req in requests:
        meta = req.metadata or {}
        dur = meta.get("duration_ms")
        if dur is None:
            continue
        try:
            dur = float(dur)
        except (TypeError, ValueError):
            continue
        if dur > threshold:
            click.echo(f"{req.id}  {dur:.1f} ms  {req.method}  {req.url}")
            found = True

    if not found:
        click.echo("No requests exceeded the threshold.")
