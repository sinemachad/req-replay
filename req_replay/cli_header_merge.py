"""CLI commands for merging headers across captured requests."""
from __future__ import annotations

import click

from req_replay.header_merge import merge_headers
from req_replay.storage import RequestStore


@click.group("header-merge")
def header_merge_group() -> None:
    """Merge headers from multiple captured requests."""


def _parse_kv(items: tuple[str, ...]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise click.BadParameter(f"Expected key=value, got {item!r}")
        k, _, v = item.partition("=")
        out[k.strip()] = v.strip()
    return out


@header_merge_group.command("run")
@click.argument("ids", nargs=-1, required=True)
@click.option("--store", "store_path", default=".req_replay", show_default=True)
@click.option(
    "--strategy",
    type=click.Choice(["first", "last", "union"]),
    default="first",
    show_default=True,
    help="Conflict resolution strategy.",
)
@click.option("--extra", multiple=True, metavar="KEY=VALUE", help="Extra headers to inject.")
def run_cmd(ids: tuple[str, ...], store_path: str, strategy: str, extra: tuple[str, ...]) -> None:
    """Merge headers from the given request IDs."""
    store = RequestStore(store_path)
    requests = []
    for rid in ids:
        try:
            requests.append(store.load(rid))
        except FileNotFoundError:
            raise click.ClickException(f"Request not found: {rid}")

    extra_headers = _parse_kv(extra) if extra else None
    result = merge_headers(requests, strategy=strategy, extra=extra_headers)
    click.echo(result.display())
    if result.has_conflicts:
        raise SystemExit(1)
