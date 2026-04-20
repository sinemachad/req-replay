"""CLI commands for header policy enforcement."""
from __future__ import annotations

import click

from req_replay.header_policy import check_header_policy, scan_header_policy
from req_replay.storage import RequestStore


@click.group("header-policy")
def header_policy_group() -> None:
    """Enforce header presence / absence rules."""


@header_policy_group.command("check")
@click.argument("request_id")
@click.option("--store", default=".req_store", show_default=True, help="Path to request store.")
@click.option(
    "--require",
    multiple=True,
    metavar="HEADER",
    help="Header that must be present (repeatable).",
)
@click.option(
    "--forbid",
    multiple=True,
    metavar="HEADER",
    help="Header that must be absent (repeatable).",
)
def check_cmd(request_id: str, store: str, require: tuple, forbid: tuple) -> None:
    """Check a single request against header policy."""
    s = RequestStore(store)
    try:
        req = s.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    result = check_header_policy(
        req,
        required=list(require) or None,
        forbidden=list(forbid) or None,
    )
    click.echo(result.summary())
    for w in result.warnings:
        click.echo(f"  [{w.code}] {w.message}")
    if not result.passed():
        raise SystemExit(1)


@header_policy_group.command("scan")
@click.option("--store", default=".req_store", show_default=True, help="Path to request store.")
@click.option(
    "--require",
    multiple=True,
    metavar="HEADER",
    help="Header that must be present (repeatable).",
)
@click.option(
    "--forbid",
    multiple=True,
    metavar="HEADER",
    help="Header that must be absent (repeatable).",
)
def scan_cmd(store: str, require: tuple, forbid: tuple) -> None:
    """Scan all stored requests against header policy."""
    s = RequestStore(store)
    requests = s.list()
    if not requests:
        click.echo("No requests found.")
        return

    results = scan_header_policy(
        requests,
        required=list(require) or None,
        forbidden=list(forbid) or None,
    )
    failed = 0
    for r in results:
        click.echo(r.summary())
        for w in r.warnings:
            click.echo(f"  [{w.code}] {w.message}")
        if not r.passed():
            failed += 1

    click.echo(f"\n{len(results)} request(s) scanned, {failed} failed.")
    if failed:
        raise SystemExit(1)
