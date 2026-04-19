"""CLI commands for retry budget management."""
from __future__ import annotations

import click

from req_replay.retry import RetryConfig, retry_replay
from req_replay.retry_budget import RetryBudget
from req_replay.storage import RequestStore


@click.group("retry-budget")
def retry_budget_group() -> None:
    """Replay multiple requests within a shared retry budget."""


@retry_budget_group.command("run")
@click.argument("store_path")
@click.option("--max-retries", default=10, show_default=True, help="Total retry budget.")
@click.option("--per-request", default=3, show_default=True, help="Max retries per request.")
@click.option("--delay", default=1.0, show_default=True, help="Delay between retries (s).")
def run_cmd(store_path: str, max_retries: int, per_request: int, delay: float) -> None:
    """Replay all stored requests within a shared retry budget."""
    store = RequestStore(store_path)
    ids = store.list_ids()
    if not ids:
        click.echo("No requests found.")
        return

    budget = RetryBudget(max_total_retries=max_retries)
    cfg = RetryConfig(max_attempts=per_request, delay_seconds=delay)

    for rid in ids:
        if budget.exhausted:
            click.echo(f"Budget exhausted — skipping remaining requests.")
            break
        req = store.load(rid)
        result = retry_replay(req, cfg)
        ok = budget.consume(rid, result.attempts, result.passed)
        status = "PASS" if result.passed else "FAIL"
        budget_warn = " [budget exceeded]" if not ok else ""
        click.echo(f"[{status}] {rid} ({result.attempts} attempt(s)){budget_warn}")

    click.echo("")
    click.echo(budget.summary())


@retry_budget_group.command("summary")
@click.argument("store_path")
@click.option("--max-retries", default=10, show_default=True)
@click.option("--per-request", default=3, show_default=True)
def summary_cmd(store_path: str, max_retries: int, per_request: int) -> None:
    """Show retry budget summary without replaying."""
    store = RequestStore(store_path)
    ids = store.list_ids()
    click.echo(f"Requests in store : {len(ids)}")
    click.echo(f"Max total retries : {max_retries}")
    click.echo(f"Max per request   : {per_request}")
    click.echo(f"Worst-case retries: {len(ids) * (per_request - 1)}")
