"""Main CLI entry-point for req-replay."""
import click

from req_replay.storage import RequestStore
from req_replay.capture import capture_request
from req_replay.replay import replay_request
from req_replay.cli_assert import assert_group
from req_replay.cli_transform import transform_group
from req_replay.cli_watch import watch_group
from req_replay.cli_compare import compare_group
from req_replay.cli_schedule import schedule_group
from req_replay.cli_tag import tag_group
from req_replay.cli_group import group_cmd


@click.group()
def cli():
    """req-replay: capture, store, and replay HTTP requests."""


@cli.command()
@click.argument("url")
@click.option("--method", "-m", default="GET", show_default=True)
@click.option("--header", "-H", multiple=True, help="Header in Key:Value format.")
@click.option("--body", "-b", default=None)
@click.option("--tag", "-t", multiple=True)
@click.option("--store-path", default=".req_replay", show_default=True)
def capture(url, method, header, body, tag, store_path):
    """Capture and store an HTTP request/response pair."""
    headers = {}
    for h in header:
        if ":" in h:
            k, v = h.split(":", 1)
            headers[k.strip()] = v.strip()

    store = RequestStore(store_path)
    req, resp = capture_request(
        method=method,
        url=url,
        headers=headers,
        body=body,
        tags=list(tag),
        store=store,
    )
    click.echo(f"Captured {req.id}  {method} {url}  -> {resp.status_code}")


@cli.command()
@click.argument("request_id")
@click.option("--store-path", default=".req_replay", show_default=True)
def replay(request_id, store_path):
    """Replay a previously captured request."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)
    result = replay_request(req)
    click.echo(result.summary())


@cli.command(name="list")
@click.option("--store-path", default=".req_replay", show_default=True)
def list_requests(store_path):
    """List all stored request IDs."""
    store = RequestStore(store_path)
    ids = store.list_ids()
    if not ids:
        click.echo("No requests stored.")
        return
    for rid in ids:
        click.echo(rid)


cli.add_command(assert_group, name="assert")
cli.add_command(transform_group, name="transform")
cli.add_command(watch_group, name="watch")
cli.add_command(compare_group, name="compare")
cli.add_command(schedule_group, name="schedule")
cli.add_command(tag_group, name="tag")
cli.add_command(group_cmd, name="group")
