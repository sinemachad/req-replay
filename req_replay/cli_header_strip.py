"""CLI commands for stripping headers from stored requests."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import click

from req_replay.header_strip import DEFAULT_STRIP_HEADERS, strip_request_headers
from req_replay.storage import RequestStore


@click.group("header-strip")
def header_strip_group() -> None:
    """Strip unwanted headers from requests."""


@header_strip_group.command("check")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option(
    "--strip",
    "extra_strip",
    multiple=True,
    help="Additional header names to strip (repeatable).",
)
@click.option(
    "--no-defaults",
    is_flag=True,
    default=False,
    help="Disable stripping of default headers.",
)
def check_cmd(
    request_id: str,
    store_path: str,
    extra_strip: tuple,
    no_defaults: bool,
) -> None:
    """Preview which headers would be stripped from REQUEST_ID."""
    store = RequestStore(Path(store_path))
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    _, result = strip_request_headers(
        req,
        strip=list(extra_strip) or None,
        use_defaults=not no_defaults,
    )
    click.echo(result.display())


@header_strip_group.command("apply")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option(
    "--strip",
    "extra_strip",
    multiple=True,
    help="Additional header names to strip (repeatable).",
)
@click.option(
    "--no-defaults",
    is_flag=True,
    default=False,
    help="Disable stripping of default headers.",
)
def apply_cmd(
    request_id: str,
    store_path: str,
    extra_strip: tuple,
    no_defaults: bool,
) -> None:
    """Strip headers from REQUEST_ID and save the updated request."""
    store = RequestStore(Path(store_path))
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    new_req, result = strip_request_headers(
        req,
        strip=list(extra_strip) or None,
        use_defaults=not no_defaults,
    )
    store.save(new_req)
    click.echo(result.display())
    if result.changed:
        click.echo("Request updated.")
