"""CLI commands for managing request groups."""
import click

from req_replay.storage import RequestStore
from req_replay import group as grp


@click.group(name="group")
def group_cmd():
    """Manage named groups of captured requests."""


@group_cmd.command("create")
@click.argument("name")
@click.option("--description", "-d", default="", help="Optional description.")
@click.option("--store-path", default=".req_replay", show_default=True)
def create_cmd(name: str, description: str, store_path: str):
    """Create a new empty group called NAME."""
    store = RequestStore(store_path)
    g = grp.create_group(store, name, description)
    click.echo(f"Created group '{g.name}'.")


@group_cmd.command("add")
@click.argument("name")
@click.argument("request_id")
@click.option("--store-path", default=".req_replay", show_default=True)
def add_cmd(name: str, request_id: str, store_path: str):
    """Add REQUEST_ID to group NAME."""
    store = RequestStore(store_path)
    try:
        g = grp.add_to_group(store, name, request_id)
        click.echo(f"Added {request_id} to group '{g.name}' ({len(g.request_ids)} total).")
    except KeyError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)


@group_cmd.command("remove")
@click.argument("name")
@click.argument("request_id")
@click.option("--store-path", default=".req_replay", show_default=True)
def remove_cmd(name: str, request_id: str, store_path: str):
    """Remove REQUEST_ID from group NAME."""
    store = RequestStore(store_path)
    try:
        g = grp.remove_from_group(store, name, request_id)
        click.echo(f"Removed {request_id} from group '{g.name}'.")
    except KeyError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)


@group_cmd.command("list")
@click.option("--store-path", default=".req_replay", show_default=True)
def list_cmd(store_path: str):
    """List all group names."""
    store = RequestStore(store_path)
    names = grp.list_groups(store)
    if not names:
        click.echo("No groups found.")
        return
    for name in names:
        click.echo(name)


@group_cmd.command("show")
@click.argument("name")
@click.option("--store-path", default=".req_replay", show_default=True)
def show_cmd(name: str, store_path: str):
    """Show details of group NAME."""
    store = RequestStore(store_path)
    try:
        g = grp.get_group(store, name)
    except KeyError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)
    click.echo(f"Group : {g.name}")
    if g.description:
        click.echo(f"Desc  : {g.description}")
    click.echo(f"Count : {len(g.request_ids)}")
    for rid in g.request_ids:
        click.echo(f"  - {rid}")
