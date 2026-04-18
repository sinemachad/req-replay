"""CLI commands for request maturity scoring."""
import click
from req_replay.storage import RequestStore
from req_replay.maturity import score_request


@click.group("maturity")
def maturity_group() -> None:
    """Score how complete / well-formed captured requests are."""


@maturity_group.command("score")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_store", show_default=True)
def score_cmd(request_id: str, store_path: str) -> None:
    """Score a single captured request."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)
    result = score_request(req)
    click.echo(result.display())


@maturity_group.command("report")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option("--min-score", default=0, show_default=True, help="Only show requests below this score.")
def report_cmd(store_path: str, min_score: int) -> None:
    """Score all stored requests and print a summary table."""
    store = RequestStore(store_path)
    requests = store.list()
    if not requests:
        click.echo("No requests found.")
        return
    results = [score_request(r) for r in requests]
    if min_score:
        results = [r for r in results if r.score < min_score]
    if not results:
        click.echo("All requests meet the minimum score threshold.")
        return
    click.echo(f"{'ID':<38} {'Score':>5}  {'Grade':>5}  Issues")
    click.echo("-" * 70)
    for res in sorted(results, key=lambda r: r.score):
        issues = ", ".join(i.code for i in res.issues) or "-"
        click.echo(f"{res.request_id:<38} {res.score:>5}  {res.grade:>5}  {issues}")
