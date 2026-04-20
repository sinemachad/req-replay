"""CLI commands for response time analysis."""
from __future__ import annotations

import click

from req_replay.response_time import analyze_response_times
from req_replay.storage import RequestStore


@click.group("response-time")
def response_time_group() -> None:
    """Analyse response time distribution across captured requests."""


@response_time_group.command("analyze")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option("--method", default=None, help="Filter by HTTP method (e.g. GET).")
def analyze_cmd(store_path: str, method: str | None) -> None:
    """Show response time distribution for stored requests."""
    store = RequestStore(store_path)
    requests = store.list()
    if method:
        requests = [r for r in requests if r.method.upper() == method.upper()]
    if not requests:
        click.echo("No requests found.")
        return
    report = analyze_response_times(requests)
    click.echo(report.display())


@response_time_group.command("slow")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option("--threshold", "threshold_ms", default=500, show_default=True, type=int,
              help="Minimum duration in ms to be considered slow.")
def slow_cmd(store_path: str, threshold_ms: int) -> None:
    """List requests that exceeded the given response time threshold."""
    store = RequestStore(store_path)
    requests = store.list()
    slow = []
    for req in requests:
        meta = req.metadata or {}
        dur = meta.get("duration_ms") or meta.get("elapsed_ms")
        try:
            if dur is not None and float(dur) >= threshold_ms:
                slow.append((req, float(dur)))
        except (TypeError, ValueError):
            pass
    if not slow:
        click.echo(f"No requests exceeded {threshold_ms}ms.")
        return
    slow.sort(key=lambda x: x[1], reverse=True)
    click.echo(f"{'ID':<36}  {'Method':<8}  {'URL':<45}  {'ms':>8}")
    click.echo("-" * 100)
    for req, dur in slow:
        click.echo(f"{req.id:<36}  {req.method:<8}  {req.url[:45]:<45}  {dur:>8.1f}")
