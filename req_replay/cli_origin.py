"""CLI commands for origin analysis."""
from __future__ import annotations
import click
from req_replay.storage import RequestStore
from req_replay.origin import analyze_origins


@click.group("origin")
def origin_group() -> None:
    """Analyze request origins."""


@origin_group.command("analyze")
@click.option("--store", "store_path", required=True, help="Path to request store.")
@click.option("--top", default=5, show_default=True, help="Number of top entries to show.")
@click.option("--method", default=None, help="Filter by HTTP method.")
def analyze_cmd(store_path: str, top: int, method: str | None) -> None:
    """Show top IPs, referers, and user-agents."""
    store = RequestStore(store_path)
    requests = store.list()
    if method:
        requests = [r for r in requests if r.method.upper() == method.upper()]
    stats = analyze_origins(requests, top_n=top)
    click.echo(stats.display())


@origin_group.command("ips")
@click.option("--store", "store_path", required=True, help="Path to request store.")
@click.option("--top", default=10, show_default=True)
def ips_cmd(store_path: str, top: int) -> None:
    """List top source IPs."""
    store = RequestStore(store_path)
    stats = analyze_origins(store.list(), top_n=top)
    if not stats.top_ips:
        click.echo("No IP data found.")
        return
    for ip, count in stats.top_ips:
        click.echo(f"{ip}\t{count}")
