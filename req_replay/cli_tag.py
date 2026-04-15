"""CLI commands for managing request tags."""
from __future__ import annotations

import click

from req_replay.storage import RequestStore
from req_replay.tag import add_tags, remove_tags, summarize_tags


@click.group(name="tag")
def tag_group() -> None:
    """Manage tags on captured requests."""


@tag_group.command("add")
@click.argument("request_id")
@click.argument("tags", nargs=-1, required=True)
@click.option("--store-dir", default=".req_replay", show_default=True)
def add_cmd(request_id: str, tags: tuple[str, ...], store_dir: str) -> None:
    """Add one or more TAGS to a captured request."""
    store = RequestStore(store_dir)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)
    updated = add_tags(req, tags)
    store.save(updated)
    click.echo(f"Tags on {request_id}: {updated.tags}")


@tag_group.command("remove")
@click.argument("request_id")
@click.argument("tags", nargs=-1, required=True)
@click.option("--store-dir", default=".req_replay", show_default=True)
def remove_cmd(request_id: str, tags: tuple[str, ...], store_dir: str) -> None:
    """Remove one or more TAGS from a captured request."""
    store = RequestStore(store_dir)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)
    updated = remove_tags(req, tags)
    store.save(updated)
    click.echo(f"Tags on {request_id}: {updated.tags}")


@tag_group.command("summary")
@click.option("--store-dir", default=".req_replay", show_default=True)
def summary_cmd(store_dir: str) -> None:
    """Show a summary of all tags across stored requests."""
    store = RequestStore(store_dir)
    requests = store.list()
    summaries = summarize_tags(requests)
    if not summaries:
        click.echo("No tags found.")
        return
    for s in summaries:
        click.echo(s.display())
