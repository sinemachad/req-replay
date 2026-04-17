"""CLI commands for parameter analysis."""
import click
from pathlib import Path

from req_replay.storage import RequestStore
from req_replay.param import analyze_params


@click.group("param")
def param_group() -> None:
    """Inspect and analyze request parameters."""


@param_group.command("show")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_store", show_default=True)
def show_cmd(request_id: str, store_path: str) -> None:
    """Show extracted parameters for a captured request."""
    store = RequestStore(Path(store_path))
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Error: request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    summary = analyze_params(req)
    click.echo(summary.display())


@param_group.command("list")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option("--has-query", is_flag=True, default=False, help="Only show requests with query params")
@click.option("--has-body", is_flag=True, default=False, help="Only show requests with body params")
def list_cmd(store_path: str, has_query: bool, has_body: bool) -> None:
    """List parameter summaries for all stored requests."""
    store = RequestStore(Path(store_path))
    requests = store.list_all()

    if not requests:
        click.echo("No requests found.")
        return

    shown = 0
    for req in requests:
        summary = analyze_params(req)
        if has_query and not summary.query_params:
            continue
        if has_body and not summary.body_params:
            continue
        click.echo(summary.display())
        click.echo("---")
        shown += 1

    if shown == 0:
        click.echo("No matching requests.")
