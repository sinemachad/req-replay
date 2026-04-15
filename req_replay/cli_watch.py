"""CLI commands for the watch feature."""
from __future__ import annotations

import click

from req_replay.storage import RequestStore
from req_replay.watch import WatchConfig, WatchEvent, watch_request


@click.group(name="watch")
def watch_group() -> None:  # noqa: D401
    """Repeatedly replay a request and report results."""


@watch_group.command("run")
@click.argument("request_id")
@click.option("--store-dir", default=".req_replay", show_default=True, help="Storage directory.")
@click.option("--interval", default=5.0, show_default=True, type=float, help="Seconds between replays.")
@click.option("--max", "max_iterations", default=None, type=int, help="Stop after N iterations.")
@click.option("--stop-on-failure", is_flag=True, default=False, help="Stop as soon as a replay fails.")
@click.option("--ignore-header", "ignore_headers", multiple=True, help="Header names to ignore when comparing.")
def run_watch(
    request_id: str,
    store_dir: str,
    interval: float,
    max_iterations: int | None,
    stop_on_failure: bool,
    ignore_headers: tuple[str, ...],
) -> None:
    """Watch REQUEST_ID and replay it on a fixed interval."""
    store = RequestStore(store_dir)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        raise click.ClickException(f"Request '{request_id}' not found in {store_dir}")

    config = WatchConfig(
        interval_seconds=interval,
        max_iterations=max_iterations,
        stop_on_failure=stop_on_failure,
        ignore_headers=list(ignore_headers),
    )

    click.echo(f"Watching request {request_id} every {interval}s …  (Ctrl-C to stop)")

    def _print_event(event: WatchEvent) -> None:
        line = event.summary()
        color = "green" if event.passed else "red"
        click.echo(click.style(line, fg=color))

    try:
        events = watch_request(req, config, on_event=_print_event)
    except KeyboardInterrupt:
        click.echo("\nWatch session interrupted.")
        return

    passed = sum(1 for e in events if e.passed)
    click.echo(f"\nDone — {passed}/{len(events)} passed.")
