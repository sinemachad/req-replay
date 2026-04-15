"""CLI commands for snapshot management."""
from __future__ import annotations

from pathlib import Path

import click

from req_replay.storage import RequestStore
from req_replay.replay import replay_request
from req_replay.snapshot import assert_snapshot, delete_snapshot, _SNAPSHOT_DIR


@click.group("snapshot")
def snapshot_group() -> None:
    """Snapshot baseline management."""


@snapshot_group.command("run")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
@click.option("--snapshot-dir", default=str(_SNAPSHOT_DIR), show_default=True)
@click.option("--update", is_flag=True, default=False, help="Overwrite existing baseline.")
@click.option("--snapshot-id", default=None, help="Custom snapshot id (defaults to request_id).")
def run_snapshot(
    request_id: str,
    store_path: str,
    snapshot_dir: str,
    update: bool,
    snapshot_id: str | None,
) -> None:
    """Replay a request and compare the response to its snapshot baseline."""
    store = RequestStore(Path(store_path))
    try:
        captured = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Error: request '{request_id}' not found.", err=True)
        raise SystemExit(1)

    result = replay_request(captured)
    sid = snapshot_id or request_id
    snap = assert_snapshot(
        snapshot_id=sid,
        response=result.actual,
        base_dir=Path(snapshot_dir),
        update=update,
    )
    click.echo(snap.summary)
    if not snap.passed:
        raise SystemExit(1)


@snapshot_group.command("delete")
@click.argument("snapshot_id")
@click.option("--snapshot-dir", default=str(_SNAPSHOT_DIR), show_default=True)
def delete_cmd(snapshot_id: str, snapshot_dir: str) -> None:
    """Delete a stored snapshot baseline."""
    removed = delete_snapshot(snapshot_id, base_dir=Path(snapshot_dir))
    if removed:
        click.echo(f"Snapshot '{snapshot_id}' deleted.")
    else:
        click.echo(f"Snapshot '{snapshot_id}' not found.", err=True)
        raise SystemExit(1)
