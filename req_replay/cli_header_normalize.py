"""CLI commands for header normalization."""
from __future__ import annotations

import click

from req_replay.header_normalize import normalize_headers, normalize_request_headers
from req_replay.storage import RequestStore


@click.group("header-normalize")
def header_normalize_group() -> None:
    """Normalize HTTP headers in captured requests."""


@header_normalize_group.command("check")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option("--canonical-only", is_flag=True, default=False,
              help="Keep only well-known canonical headers.")
def check_cmd(request_id: str, store_path: str, canonical_only: bool) -> None:
    """Show normalization changes for a single request without saving."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Error: request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    result = normalize_headers(
        req.headers,
        canonical_only=canonical_only,
    )
    click.echo(result.display())


@header_normalize_group.command("apply")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option("--canonical-only", is_flag=True, default=False,
              help="Keep only well-known canonical headers.")
def apply_cmd(request_id: str, store_path: str, canonical_only: bool) -> None:
    """Normalize headers of a stored request and save the result."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Error: request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    result = normalize_headers(req.headers, canonical_only=canonical_only)
    new_req = normalize_request_headers(req, canonical_only=False)
    if canonical_only:
        # Re-run with canonical_only flag respected
        from req_replay.header_normalize import normalize_headers as _nh
        import copy
        r2 = _nh(req.headers, canonical_only=True)
        new_req2 = copy.deepcopy(req)
        new_req2.headers = r2.normalized
        store.save(new_req2)
        click.echo(result.display())
        return

    store.save(new_req)
    click.echo(result.display())
    if result.changed:
        click.echo(f"Saved updated request '{request_id}'.")
    else:
        click.echo("No changes made.")
