"""CLI commands for header template rendering."""
from __future__ import annotations

import click

from req_replay.header_template import render_headers, render_request_headers
from req_replay.storage import RequestStore


@click.group("header-template")
def header_template_group() -> None:
    """Apply variable substitution to request headers."""


def _parse_kv(pairs: tuple[str, ...]) -> dict[str, str]:
    result: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise click.BadParameter(f"Expected KEY=VALUE, got: {pair!r}")
        k, _, v = pair.partition("=")
        result[k.strip()] = v.strip()
    return result


@header_template_group.command("check")
@click.argument("request_id")
@click.option("-v", "--var", "variables", multiple=True, metavar="KEY=VALUE",
              help="Variable substitution (repeatable).")
@click.option("--store", "store_path", default=".req_store", show_default=True)
def check_cmd(
    request_id: str,
    variables: tuple[str, ...],
    store_path: str,
) -> None:
    """Preview header substitutions for a stored request."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request {request_id!r} not found.", err=True)
        raise SystemExit(1)

    vars_dict = _parse_kv(variables)
    result = render_headers(req.headers, vars_dict)
    if result.changed:
        click.echo(result.display())
    else:
        click.echo("No substitutions made.")


@header_template_group.command("apply")
@click.argument("request_id")
@click.option("-v", "--var", "variables", multiple=True, metavar="KEY=VALUE",
              help="Variable substitution (repeatable).")
@click.option("--store", "store_path", default=".req_store", show_default=True)
def apply_cmd(
    request_id: str,
    variables: tuple[str, ...],
    store_path: str,
) -> None:
    """Apply header substitutions and save the updated request."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request {request_id!r} not found.", err=True)
        raise SystemExit(1)

    vars_dict = _parse_kv(variables)
    updated = render_request_headers(req, vars_dict)
    store.save(updated)
    result = render_headers(req.headers, vars_dict)
    if result.changed:
        click.echo(f"Applied {len(result.substitutions)} substitution(s) and saved.")
        click.echo(result.display())
    else:
        click.echo("No substitutions made; request unchanged.")
