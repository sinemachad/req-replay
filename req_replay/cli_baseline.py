"""CLI commands for baseline management."""
from __future__ import annotations

from pathlib import Path

import click

from req_replay.baseline import (
    save_baseline,
    delete_baseline,
    list_baselines,
    compare_to_baseline,
)
from req_replay.storage import RequestStore
from req_replay.replay import replay_request


@click.group("baseline")
def baseline_group() -> None:
    """Manage response baselines."""


@baseline_group.command("save")
@click.argument("request_id")
@click.option("--store", "store_dir", default=".req_store", show_default=True)
def save_cmd(request_id: str, store_dir: str) -> None:
    """Replay a request and save the response as its baseline."""
    store = RequestStore(Path(store_dir))
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)
    result = replay_request(req)
    path = save_baseline(Path(store_dir), request_id, result.actual)
    click.echo(f"Baseline saved: {path}")


@baseline_group.command("check")
@click.argument("request_id")
@click.option("--store", "store_dir", default=".req_store", show_default=True)
@click.option("--ignore-header", "ignore_headers", multiple=True)
def check_cmd(request_id: str, store_dir: str, ignore_headers: tuple[str, ...]) -> None:
    """Replay a request and compare the response to its baseline."""
    store = RequestStore(Path(store_dir))
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)
    result = replay_request(req)
    try:
        baseline_result = compare_to_baseline(
            Path(store_dir), request_id, result.actual, list(ignore_headers)
        )
    except FileNotFoundError:
        click.echo(f"No baseline found for '{request_id}'.", err=True)
        raise SystemExit(1)
    click.echo(baseline_result.summary())
    if not baseline_result.passed:
        raise SystemExit(1)


@baseline_group.command("delete")
@click.argument("request_id")
@click.option("--store", "store_dir", default=".req_store", show_default=True)
def delete_cmd(request_id: str, store_dir: str) -> None:
    """Delete a stored baseline."""
    removed = delete_baseline(Path(store_dir), request_id)
    if removed:
        click.echo(f"Baseline for '{request_id}' deleted.")
    else:
        click.echo(f"No baseline found for '{request_id}'.")


@baseline_group.command("list")
@click.option("--store", "store_dir", default=".req_store", show_default=True)
def list_cmd(store_dir: str) -> None:
    """List all stored baselines."""
    ids = list_baselines(Path(store_dir))
    if not ids:
        click.echo("No baselines stored.")
    else:
        for rid in ids:
            click.echo(rid)
