"""CLI commands for header injection."""
from __future__ import annotations

import click

from req_replay.header_inject import inject_headers
from req_replay.storage import RequestStore


@click.group("header-inject")
def header_inject_group() -> None:
    """Inject or override headers on stored requests."""


def _parse_kv(pairs: tuple[str, ...]) -> dict[str, str]:
    result: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise click.BadParameter(f"Expected KEY=VALUE, got: {pair!r}")
        k, _, v = pair.partition("=")
        result[k.strip()] = v.strip()
    return result


@header_inject_group.command("apply")
@click.argument("request_id")
@click.argument("headers", nargs=-1, required=True, metavar="KEY=VALUE...")
@click.option(
    "--no-overwrite",
    is_flag=True,
    default=False,
    help="Skip headers that already exist on the request.",
)
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option("--save", is_flag=True, default=False, help="Persist changes back to the store.")
def apply_cmd(
    request_id: str,
    headers: tuple[str, ...],
    no_overwrite: bool,
    store_path: str,
    save: bool,
) -> None:
    """Inject KEY=VALUE headers into a stored request."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    try:
        inject_map = _parse_kv(headers)
    except click.BadParameter as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)

    new_req, result = inject_headers(req, inject_map, overwrite=not no_overwrite)
    click.echo(result.display())

    if save:
        store.save(new_req)
        click.echo("Saved.")
