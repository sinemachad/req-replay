"""Main CLI entry-point for req-replay."""
from __future__ import annotations

import json

import click

from req_replay.capture import capture_request
from req_replay.cli_assert import assert_group
from req_replay.cli_compare import compare_group
from req_replay.cli_group import group_cmd
from req_replay.cli_retry import retry_group
from req_replay.cli_schedule import schedule_group
from req_replay.cli_tag import tag_group
from req_replay.cli_transform import transform_group
from req_replay.cli_watch import watch_group
from req_replay.replay import replay_request
from req_replay.storage import RequestStore


@click.group()
def cli() -> None:
    """req-replay: capture, store, and replay HTTP requests."""


@cli.command()
@click.argument("method")
@click.argument("url")
@click.option("--header", "-H", multiple=True, help="Header in 'Key: Value' format.")
@click.option("--body", "-d", default=None, help="Request body.")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
@click.option("--tag", multiple=True, help="Tags to attach to the captured request.")
def capture(method: str, url: str, header: tuple, body: str | None, store_path: str, tag: tuple) -> None:
    """Capture an HTTP request and store it."""
    headers = {}
    for h in header:
        if ":" in h:
            k, _, v = h.partition(":")
            headers[k.strip()] = v.strip()

    store = RequestStore(store_path)
    req, resp = capture_request(
        method=method,
        url=url,
        headers=headers,
        body=body.encode() if body else None,
        tags=list(tag),
        store=store,
    )
    click.echo(f"Captured {req.id}  {req.method} {req.url}  -> {resp.status_code}")


@cli.command()
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
@click.option("--base-url", default=None, help="Override base URL.")
def replay(request_id: str, store_path: str, base_url: str | None) -> None:
    """Replay a stored request and compare with the original response."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Error: request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    result = replay_request(req, base_url=base_url)
    click.echo(result.summary)
    if not result.passed:
        raise SystemExit(1)


@cli.command("list")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
@click.option("--method", default=None, help="Filter by HTTP method.")
def list_requests(store_path: str, method: str | None) -> None:
    """List stored requests."""
    store = RequestStore(store_path)
    requests = store.list()
    if method:
        requests = [r for r in requests if r.method.upper() == method.upper()]
    if not requests:
        click.echo("No requests found.")
        return
    for req in requests:
        tags = f"  [{', '.join(req.tags)}]" if req.tags else ""
        click.echo(f"{req.id}  {req.method:6s}  {req.url}{tags}")


cli.add_command(assert_group, name="assert")
cli.add_command(compare_group, name="compare")
cli.add_command(group_cmd, name="group")
cli.add_command(retry_group, name="retry")
cli.add_command(schedule_group, name="schedule")
cli.add_command(tag_group, name="tag")
cli.add_command(transform_group, name="transform")
cli.add_command(watch_group, name="watch")
