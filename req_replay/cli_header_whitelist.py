"""CLI commands for header whitelist enforcement."""
from __future__ import annotations

import click

from req_replay.header_whitelist import check_whitelist, scan_whitelist, _DEFAULT_ALLOWED
from req_replay.storage import RequestStore


@click.group("header-whitelist")
def header_whitelist_group() -> None:
    """Enforce an allowed-header whitelist on captured requests."""


def _allowed_set(extra: tuple[str, ...], strict: bool) -> set[str] | None:
    if strict:
        return {h.lower() for h in extra} if extra else set()
    if extra:
        return _DEFAULT_ALLOWED | {h.lower() for h in extra}
    return None  # use default


@header_whitelist_group.command("check")
@click.argument("request_id")
@click.argument("store_path", envvar="RR_STORE")
@click.option("--allow", "extra", multiple=True, help="Additional allowed header names.")
@click.option("--strict", is_flag=True, help="Use only --allow headers (ignore defaults).")
def check_cmd(request_id: str, store_path: str, extra: tuple[str, ...], strict: bool) -> None:
    """Check a single request against the whitelist."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    result = check_whitelist(req, _allowed_set(extra, strict))
    click.echo(result.summary())
    for w in result.warnings:
        click.echo(f"  [{w.code}] {w.message}")


@header_whitelist_group.command("scan")
@click.argument("store_path", envvar="RR_STORE")
@click.option("--allow", "extra", multiple=True, help="Additional allowed header names.")
@click.option("--strict", is_flag=True, help="Use only --allow headers (ignore defaults).")
@click.option("--fail-fast", is_flag=True, help="Stop after first failure.")
def scan_cmd(store_path: str, extra: tuple[str, ...], strict: bool, fail_fast: bool) -> None:
    """Scan all stored requests against the whitelist."""
    store = RequestStore(store_path)
    requests = store.list()
    if not requests:
        click.echo("No requests found.")
        return

    results = scan_whitelist(requests, _allowed_set(extra, strict))
    any_fail = False
    for r in results:
        click.echo(r.summary())
        if not r.passed():
            any_fail = True
            for w in r.warnings:
                click.echo(f"  [{w.code}] {w.message}")
            if fail_fast:
                break

    if any_fail:
        raise SystemExit(1)
