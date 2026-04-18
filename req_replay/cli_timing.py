"""CLI commands for request timing analysis."""
import click
from req_replay.storage import RequestStore
from req_replay.timing import analyze_timing, summarize_timings


@click.group("timing")
def timing_group() -> None:
    """Analyse per-request timing breakdowns."""


@timing_group.command("show")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
def show_cmd(request_id: str, store_path: str) -> None:
    """Show timing breakdown for a single request."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)
    breakdown = analyze_timing(req)
    click.echo(breakdown.display())


@timing_group.command("list")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
def list_cmd(store_path: str) -> None:
    """List timing breakdowns for all requests with timing data."""
    store = RequestStore(store_path)
    requests = store.list_all()
    breakdowns = summarize_timings(requests)
    if not breakdowns:
        click.echo("No timing data found.")
        return
    for bd in breakdowns:
        meta = {}
        total = bd.total_ms
        label = f"{total:.2f} ms" if total is not None else "n/a"
        click.echo(f"{bd.request_id}  total={label}")
