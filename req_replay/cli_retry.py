"""CLI commands for retry-replay functionality."""
from __future__ import annotations

import click

from req_replay.retry import RetryConfig, retry_replay
from req_replay.storage import RequestStore


@click.group("retry")
def retry_group() -> None:
    """Replay a request with automatic retry on failure."""


@retry_group.command("run")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
@click.option("--max-attempts", default=3, show_default=True, help="Maximum retry attempts.")
@click.option("--backoff", default=1.0, show_default=True, help="Initial backoff in seconds.")
@click.option("--multiplier", default=2.0, show_default=True, help="Backoff multiplier.")
@click.option("--base-url", default=None, help="Override base URL for replay.")
@click.option("--no-diff-retry", is_flag=True, default=False, help="Don't retry on diff failure.")
def run_retry(
    request_id: str,
    store_path: str,
    max_attempts: int,
    backoff: float,
    multiplier: float,
    base_url: str | None,
    no_diff_retry: bool,
) -> None:
    """Replay REQUEST_ID with retry logic."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Error: request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    config = RetryConfig(
        max_attempts=max_attempts,
        backoff_seconds=backoff,
        backoff_multiplier=multiplier,
        retry_on_diff=not no_diff_retry,
    )

    result = retry_replay(req, config=config, base_url=base_url)

    for i, r in enumerate(result.all_results, 1):
        icon = "✓" if r.passed else "✗"
        click.echo(f"  Attempt {i}: {icon} {r.summary}")

    click.echo(result.summary)
    if not result.passed:
        raise SystemExit(1)
