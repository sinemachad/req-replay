"""CLI commands for header-prefix operations."""
from __future__ import annotations

import click

from req_replay.header_prefix import find_by_prefix, strip_request_headers_by_prefix
from req_replay.storage import RequestStore


@click.group("header-prefix")
def header_prefix_group() -> None:
    """Inspect or strip headers by key prefix."""


@header_prefix_group.command("find")
@click.argument("request_id")
@click.argument("prefix")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option("--case-sensitive", is_flag=True, default=False)
def find_cmd(
    request_id: str,
    prefix: str,
    store_path: str,
    case_sensitive: bool,
) -> None:
    """List headers in REQUEST_ID that start with PREFIX."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    matched = find_by_prefix(req.headers, prefix, case_sensitive=case_sensitive)
    if not matched:
        click.echo(f"No headers found with prefix '{prefix}'.")
        return
    for k, v in sorted(matched.items()):
        click.echo(f"{k}: {v}")


@header_prefix_group.command("strip")
@click.argument("request_id")
@click.argument("prefix")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option("--case-sensitive", is_flag=True, default=False)
@click.option("--save", "do_save", is_flag=True, default=False,
              help="Persist the stripped request back to the store.")
def strip_cmd(
    request_id: str,
    prefix: str,
    store_path: str,
    case_sensitive: bool,
    do_save: bool,
) -> None:
    """Strip headers in REQUEST_ID that start with PREFIX."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    new_req, result = strip_request_headers_by_prefix(
        req, prefix, case_sensitive=case_sensitive
    )
    click.echo(result.display())

    if do_save and result.changed:
        store.save(new_req)
        click.echo("Request updated in store.")
    elif do_save:
        click.echo("No changes — store not modified.")
