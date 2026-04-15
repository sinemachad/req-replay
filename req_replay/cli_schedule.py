"""CLI commands for scheduled replay."""
from __future__ import annotations

import click

from req_replay.schedule import ScheduleConfig, ScheduleEvent, schedule_replay
from req_replay.storage import RequestStore


@click.group("schedule")
def schedule_group() -> None:
    """Replay a stored request on a fixed interval."""


def _print_event(event: ScheduleEvent, *, verbose: bool) -> None:
    colour = "green" if event.passed else "red"
    click.echo(click.style(event.summary, fg=colour))
    if verbose and not event.passed:
        diff = event.result.diff
        if diff.status_mismatch:
            click.echo(
                f"  status: expected={diff.expected_status} "
                f"actual={diff.actual_status}"
            )
        if diff.body_mismatch:
            click.echo("  body mismatch detected")


@schedule_group.command("run")
@click.argument("request_id")
@click.option("--store-path", default=".req_replay", show_default=True)
@click.option(
    "--interval",
    default=60.0,
    show_default=True,
    help="Seconds between replays.",
)
@click.option(
    "--max-iterations",
    default=None,
    type=int,
    help="Stop after N iterations (default: run forever).",
)
@click.option(
    "--stop-on-failure",
    is_flag=True,
    default=False,
    help="Halt the schedule when a replay fails.",
)
@click.option("--verbose", "-v", is_flag=True, default=False)
def run_schedule(
    request_id: str,
    store_path: str,
    interval: float,
    max_iterations: int | None,
    stop_on_failure: bool,
    verbose: bool,
) -> None:
    """Repeatedly replay REQUEST_ID on a fixed interval."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(click.style(f"Request '{request_id}' not found.", fg="red"), err=True)
        raise SystemExit(1)

    config = ScheduleConfig(
        interval_seconds=interval,
        max_iterations=max_iterations,
        stop_on_failure=stop_on_failure,
    )

    click.echo(f"Scheduling '{request_id}' every {interval}s …  (Ctrl-C to stop)")
    try:
        for event in schedule_replay(req, config):
            _print_event(event, verbose=verbose)
    except KeyboardInterrupt:
        click.echo("\nSchedule stopped.")
