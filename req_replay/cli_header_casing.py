"""CLI commands for header casing analysis."""
from __future__ import annotations

import click

from req_replay.header_casing import analyze_casing
from req_replay.storage import RequestStore


@click.group("header-casing")
def header_casing_group() -> None:
    """Analyse and enforce header key casing conventions."""


@header_casing_group.command("check")
@click.argument("request_id")
@click.option(
    "--convention",
    default="title",
    show_default=True,
    type=click.Choice(["title", "lower"]),
    help="Casing convention to enforce.",
)
@click.option("--store", default=".req_store", show_default=True)
def check_cmd(request_id: str, convention: str, store: str) -> None:
    """Check a single request's header casing."""
    s = RequestStore(store)
    try:
        req = s.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    result = analyze_casing(req, convention=convention)
    if result.passed:
        click.echo(f"OK – all headers follow {convention!r} convention.")
    else:
        click.echo(f"FAIL – {len(result.warnings)} casing issue(s) found:")
        for w in result.warnings:
            click.echo(f"  [{w.code}] '{w.actual}' → expected '{w.expected}'")
        raise SystemExit(1)


@header_casing_group.command("scan")
@click.option(
    "--convention",
    default="title",
    show_default=True,
    type=click.Choice(["title", "lower"]),
)
@click.option("--store", default=".req_store", show_default=True)
def scan_cmd(convention: str, store: str) -> None:
    """Scan all stored requests for header casing issues."""
    s = RequestStore(store)
    requests = s.list()
    if not requests:
        click.echo("No requests found.")
        return

    failed = 0
    for req in requests:
        result = analyze_casing(req, convention=convention)
        click.echo(result.summary())
        if not result.passed:
            failed += 1

    click.echo(f"\n{len(requests)} checked, {failed} failed.")
    if failed:
        raise SystemExit(1)
