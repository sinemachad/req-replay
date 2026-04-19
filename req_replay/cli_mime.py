"""CLI commands for MIME type analysis."""
import click
from req_replay.storage import RequestStore
from req_replay.mime import analyze_mime


@click.group("mime")
def mime_group() -> None:
    """Analyse MIME types used across captured requests and responses."""


@mime_group.command("analyze")
@click.option("--store", "store_path", required=True, help="Path to request store.")
@click.option("--top", default=5, show_default=True, help="Number of top types to show.")
def analyze_cmd(store_path: str, top: int) -> None:
    """Show top MIME types for requests and responses."""
    store = RequestStore(store_path)
    requests = store.list()
    if not requests:
        click.echo("No requests found.")
        return

    pairs = []
    for req in requests:
        try:
            resp = store.load_response(req.id)
            pairs.append((req, resp))
        except Exception:
            pass

    stats = analyze_mime(pairs)
    click.echo(f"Top {top} request MIME types:")
    for mime, count in stats.top_request_types(top):
        click.echo(f"  {mime}: {count}")
    click.echo(f"Top {top} response MIME types:")
    for mime, count in stats.top_response_types(top):
        click.echo(f"  {mime}: {count}")


@mime_group.command("breakdown")
@click.option("--store", "store_path", required=True, help="Path to request store.")
def breakdown_cmd(store_path: str) -> None:
    """Show full MIME type breakdown."""
    store = RequestStore(store_path)
    requests = store.list()
    pairs = []
    for req in requests:
        try:
            resp = store.load_response(req.id)
            pairs.append((req, resp))
        except Exception:
            pass
    stats = analyze_mime(pairs)
    click.echo(stats.display())
