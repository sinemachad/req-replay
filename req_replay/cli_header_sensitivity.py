"""CLI commands for header sensitivity analysis."""
from __future__ import annotations

import click

from req_replay.header_sensitivity import analyze_sensitivity
from req_replay.storage import RequestStore


@click.group("header-sensitivity")
def header_sensitivity_group() -> None:
    """Detect sensitive headers in stored requests."""


@header_sensitivity_group.command("check")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option(
    "--extra",
    multiple=True,
    help="Additional header name patterns to flag as sensitive.",
)
def check_cmd(request_id: str, store_path: str, extra: tuple) -> None:
    """Check a single request for sensitive headers."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    result = analyze_sensitivity(request_id, req.headers, list(extra))
    click.echo(result.display())
    if not result.passed:
        raise SystemExit(1)


@header_sensitivity_group.command("scan")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option(
    "--extra",
    multiple=True,
    help="Additional header name patterns to flag as sensitive.",
)
@click.option("--fail-fast", is_flag=True, default=False)
def scan_cmd(store_path: str, extra: tuple, fail_fast: bool) -> None:
    """Scan all stored requests for sensitive headers."""
    store = RequestStore(store_path)
    requests = store.list()
    if not requests:
        click.echo("No requests found.")
        return

    any_failed = False
    for req in requests:
        result = analyze_sensitivity(req.id, req.headers, list(extra))
        click.echo(result.summary())
        if not result.passed:
            any_failed = True
            if fail_fast:
                raise SystemExit(1)

    if any_failed:
        raise SystemExit(1)
