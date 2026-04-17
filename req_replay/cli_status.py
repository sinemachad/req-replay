"""CLI commands for HTTP status code analysis."""
from __future__ import annotations

import click

from req_replay.models import CapturedResponse
from req_replay.status import analyze_status
from req_replay.storage import RequestStore


@click.group("status")
def status_group() -> None:
    """Analyse status code distribution."""


@status_group.command("analyze")
@click.option("--store", "store_path", required=True, help="Path to request store.")
@click.option("--method", default=None, help="Filter by HTTP method.")
def analyze_cmd(store_path: str, method: str | None) -> None:
    """Print status code breakdown for stored requests."""
    store = RequestStore(store_path)
    requests = store.list()

    pairs = []
    for req in requests:
        if method and req.method.upper() != method.upper():
            continue
        resp_data = req.metadata.get("response")
        if resp_data is None:
            continue
        resp = CapturedResponse(
            status_code=resp_data["status_code"],
            headers=resp_data.get("headers", {}),
            body=resp_data.get("body", ""),
            elapsed_ms=resp_data.get("elapsed_ms", 0.0),
        )
        pairs.append((req, resp))

    stats = analyze_status(pairs)
    click.echo(stats.display())


@status_group.command("codes")
@click.option("--store", "store_path", required=True, help="Path to request store.")
def codes_cmd(store_path: str) -> None:
    """List unique status codes seen."""
    store = RequestStore(store_path)
    requests = store.list()
    seen = set()
    for req in requests:
        resp_data = req.metadata.get("response")
        if resp_data:
            seen.add(resp_data["status_code"])
    if not seen:
        click.echo("No responses recorded.")
    else:
        for code in sorted(seen):
            click.echo(str(code))
