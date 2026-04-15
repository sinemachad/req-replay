"""CLI commands for comparing two stored requests."""
import click
from req_replay.storage import RequestStore
from req_replay.compare import compare_requests


@click.group(name="compare")
def compare_group():
    """Compare two captured requests."""


@compare_group.command(name="run")
@click.argument("id_a")
@click.argument("id_b")
@click.option("--store-dir", default=".req_replay", show_default=True,
              help="Directory where requests are stored.")
@click.option("--include-responses", is_flag=True, default=False,
              help="Also diff the stored responses.")
def run_compare(id_a: str, id_b: str, store_dir: str, include_responses: bool):
    """Compare request ID_A with request ID_B."""
    store = RequestStore(store_dir)

    try:
        req_a = store.load(id_a)
    except FileNotFoundError:
        click.echo(f"Error: request '{id_a}' not found.", err=True)
        raise SystemExit(1)

    try:
        req_b = store.load(id_b)
    except FileNotFoundError:
        click.echo(f"Error: request '{id_b}' not found.", err=True)
        raise SystemExit(1)

    resp_a = None
    resp_b = None

    if include_responses:
        try:
            resp_a = store.load_response(id_a)
        except (FileNotFoundError, AttributeError):
            click.echo(f"Warning: no stored response for '{id_a}'.", err=True)

        try:
            resp_b = store.load_response(id_b)
        except (FileNotFoundError, AttributeError):
            click.echo(f"Warning: no stored response for '{id_b}'.", err=True)

    result = compare_requests(req_a, req_b, resp_a, resp_b)
    click.echo(result.summary())

    if not result.requests_equivalent:
        raise SystemExit(1)
