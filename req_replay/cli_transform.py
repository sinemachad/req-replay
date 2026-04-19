"""CLI sub-commands for transforming requests before replay."""

import json
import click

from req_replay.storage import RequestStore
from req_replay.transform import TransformConfig, transform_request
from req_replay.replay import replay_request


@click.group(name="transform")
def transform_group():
    """Transform and replay captured requests."""


def _parse_kv(items):
    """Parse an iterable of 'KEY:VALUE' strings into a dict.

    Raises a ClickException if any item does not contain a colon separator.
    """
    result = {}
    for item in items:
        if ":" not in item:
            raise click.ClickException(f"Expected KEY:VALUE, got: {item!r}")
        k, v = item.split(":", 1)
        result[k.strip()] = v.strip()
    return result


@transform_group.command(name="replay")
@click.argument("request_id")
@click.option("--store-dir", default=".req_replay", show_default=True,
              help="Directory where requests are stored.")
@click.option("--base-url", default=None,
              help="Override the base URL (scheme + host) of the request.")
@click.option("--set-header", multiple=True, metavar="KEY:VALUE",
              help="Override or add a header (repeatable).")
@click.option("--remove-header", multiple=True, metavar="KEY",
              help="Remove a header before replay (repeatable).")
@click.option("--set-param", multiple=True, metavar="KEY:VALUE",
              help="Override or add a query parameter (repeatable).")
@click.option("--remove-param", multiple=True, metavar="KEY",
              help="Remove a query parameter before replay (repeatable).")
@click.option("--body", default=None, help="Override the request body.")
def replay_transformed(request_id, store_dir, base_url, set_header,
                       remove_header, set_param, remove_param, body):
    """Replay REQUEST_ID after applying transformations."""
    store = RequestStore(store_dir)
    try:
        captured = store.load(request_id)
    except FileNotFoundError:
        raise click.ClickException(f"Request '{request_id}' not found in {store_dir}")

    config = TransformConfig(
        base_url=base_url,
        override_headers=_parse_kv(set_header),
        remove_headers=list(remove_header),
        override_query_params=_parse_kv(set_param),
        remove_query_params=list(remove_param),
        override_body=body,
    )

    transformed = transform_request(captured, config)
    click.echo(f"Replaying transformed request to: {transformed.url}")

    result = replay_request(transformed, captured)
    click.echo(result.summary())

    if not result.passed:
        raise SystemExit(1)
