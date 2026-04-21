import click
from req_replay.storage import RequestStore
from req_replay.method_stats import analyze_methods


@click.group("methods")
def method_stats_group() -> None:
    """Analyse HTTP method distribution across captured requests."""


@method_stats_group.command("analyze")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
@click.option("--top", "top_n", default=0, help="Show only top N methods (0 = all).")
def analyze_cmd(store_path: str, top_n: int) -> None:
    """Print method distribution for all stored requests."""
    store = RequestStore(store_path)
    requests = store.list()
    if not requests:
        click.echo("No requests found.")
        return
    stats = analyze_methods(requests)
    if top_n > 0:
        pairs = stats.top(top_n)
        click.echo(f"Top {top_n} methods (total={stats.total}):")
        for method, count in pairs:
            pct = stats.percentages.get(method, 0.0)
            click.echo(f"  {method:<10} {count:>5}  ({pct:.1f}%)")
    else:
        click.echo(stats.display())


@method_stats_group.command("top")
@click.argument("n", default=3)
@click.option("--store", "store_path", default=".req_replay", show_default=True)
def top_cmd(n: int, store_path: str) -> None:
    """Show the top N most-used HTTP methods."""
    if n < 1:
        raise click.BadParameter("N must be a positive integer.", param_hint="'n'")
    store = RequestStore(store_path)
    requests = store.list()
    if not requests:
        click.echo("No requests found.")
        return
    stats = analyze_methods(requests)
    for method, count in stats.top(n):
        click.echo(f"{method}: {count}")
