"""CLI commands for anomaly detection."""
from __future__ import annotations

import click

from req_replay.storage import RequestStore
from req_replay.anomaly import analyze_anomalies


@click.group("anomaly")
def anomaly_group() -> None:
    """Detect anomalous requests in the store."""


@anomaly_group.command("scan")
@click.option("--store", "store_path", required=True, help="Path to request store directory.")
@click.option("--threshold", default=2.5, show_default=True, help="Z-score threshold.")
@click.option("--method", default=None, help="Filter by HTTP method.")
def scan_cmd(store_path: str, threshold: float, method: str | None) -> None:
    """Scan all stored requests for anomalies."""
    store = RequestStore(store_path)
    requests = store.list()
    if method:
        requests = [r for r in requests if r.method.upper() == method.upper()]

    if not requests:
        click.echo("No requests found.")
        return

    result = analyze_anomalies(requests, z_threshold=threshold)
    click.echo(result.summary())
    if not result.passed:
        raise SystemExit(1)


@anomaly_group.command("check")
@click.argument("request_id")
@click.option("--store", "store_path", required=True, help="Path to request store directory.")
@click.option("--threshold", default=2.5, show_default=True, help="Z-score threshold.")
def check_cmd(request_id: str, store_path: str, threshold: float) -> None:
    """Check whether a single request is anomalous relative to the rest of the store."""
    store = RequestStore(store_path)
    try:
        target = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    all_requests = store.list()
    result = analyze_anomalies(all_requests, z_threshold=threshold)
    flagged = [w for w in result.warnings if w.request_id == request_id]

    if not flagged:
        click.echo(f"Request '{request_id}' shows no anomalies.")
    else:
        for w in flagged:
            click.echo(f"[{w.field}] {w.message}")
        raise SystemExit(1)
