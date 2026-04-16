"""CLI commands for mock server management."""
from __future__ import annotations

import json
from pathlib import Path

import click

from req_replay.mock import MockRule, MockServer, build_mock_server
from req_replay.storage import RequestStore


@click.group("mock")
def mock_group() -> None:
    """Manage mock rules and serve canned responses."""


@mock_group.command("build")
@click.argument("store_path", type=click.Path())
@click.argument("output", type=click.Path())
def build_cmd(store_path: str, output: str) -> None:
    """Build a mock rule file from all stored request/response pairs."""
    store = RequestStore(Path(store_path))
    ids = store.list_ids()
    if not ids:
        click.echo("No requests found.")
        return
    pairs = []
    for rid in ids:
        req = store.load(rid)
        snap_path = Path(store_path) / "snapshots" / f"{rid}.json"
        if snap_path.exists():
            from req_replay.models import CapturedResponse
            data = json.loads(snap_path.read_text())
            resp = CapturedResponse.from_dict(data)
            pairs.append((req, resp))
    server = build_mock_server(pairs)
    rules_data = [r.to_dict() for r in server.rules]
    Path(output).write_text(json.dumps(rules_data, indent=2))
    click.echo(f"Wrote {len(rules_data)} mock rule(s) to {output}")


@mock_group.command("list")
@click.argument("rules_file", type=click.Path(exists=True))
def list_cmd(rules_file: str) -> None:
    """List mock rules from a rules file."""
    data = json.loads(Path(rules_file).read_text())
    if not data:
        click.echo("No rules defined.")
        return
    for i, r in enumerate(data, 1):
        click.echo(f"{i}. [{r['method'].upper()}] {r['path']} -> {r['response']['status_code']}")
