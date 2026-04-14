"""CLI entry point for req-replay."""

import json
import sys

import click

from req_replay.capture import capture_request
from req_replay.replay import replay_request
from req_replay.storage import RequestStore


@click.group()
@click.option("--store-dir", default=".req_replay", show_default=True, help="Storage directory.")
@click.pass_context
def cli(ctx: click.Context, store_dir: str):
    """req-replay: Capture and replay HTTP requests."""
    ctx.ensure_object(dict)
    ctx.obj["store"] = RequestStore(store_dir)


@cli.command()
@click.argument("url")
@click.option("-m", "--method", default="GET", show_default=True)
@click.option("-H", "--header", multiple=True, help="Header in Key:Value format.")
@click.option("-b", "--body", default=None, help="Request body string.")
@click.option("-t", "--tag", multiple=True, help="Tags for this request.")
@click.pass_context
def capture(ctx, url, method, header, body, tag):
    """Capture an HTTP request and store it."""
    headers = {}
    for h in header:
        if ":" in h:
            k, v = h.split(":", 1)
            headers[k.strip()] = v.strip()

    store = ctx.obj["store"]
    req, resp = capture_request(method, url, headers=headers, body=body, store=store, tags=list(tag))
    click.echo(f"Captured request {req.id} → {resp.status_code}")


@cli.command()
@click.argument("request_id")
@click.option("--url", default=None, help="Override the target URL.")
@click.pass_context
def replay(ctx, request_id, url):
    """Replay a stored HTTP request and compare responses."""
    store = ctx.obj["store"]
    result = replay_request(request_id, store, override_url=url)
    click.echo(result.summary())
    if not result.passed:
        sys.exit(1)


@cli.command(name="list")
@click.pass_context
def list_requests(ctx):
    """List all stored request IDs."""
    store = ctx.obj["store"]
    ids = store.list_ids()
    if not ids:
        click.echo("No requests stored.")
    for rid in ids:
        click.echo(rid)


if __name__ == "__main__":
    cli()
