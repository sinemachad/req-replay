"""CLI commands for generating reports."""
from __future__ import annotations

from pathlib import Path

import click

from req_replay.report import build_report, save_report_json, save_report_html
from req_replay.storage import RequestStore
from req_replay.snapshot import load_snapshot
from req_replay.diff import diff_responses


@click.group("report")
def report_group() -> None:
    """Generate replay reports."""


@report_group.command("run")
@click.option("--store", "store_path", required=True, type=click.Path(), help="Request store directory.")
@click.option("--format", "fmt", default="json", type=click.Choice(["json", "html"]), show_default=True)
@click.option("--output", "-o", required=True, type=click.Path(), help="Output file path.")
def run_report(store_path: str, fmt: str, output: str) -> None:
    """Compare stored snapshots against originals and write a report."""
    store = RequestStore(Path(store_path))
    ids = store.list_ids()
    if not ids:
        click.echo("No requests found in store.")
        return

    pairs = []
    skipped = 0
    for rid in ids:
        req = store.load(rid)
        try:
            snapshot = load_snapshot(Path(store_path), rid)
        except FileNotFoundError:
            skipped += 1
            continue
        original = req.response  # type: ignore[attr-defined]
        if original is None:
            skipped += 1
            continue
        diff = diff_responses(snapshot, original)
        pairs.append((rid, req.method, req.url, diff))

    report = build_report(pairs)
    out_path = Path(output)
    if fmt == "json":
        save_report_json(report, out_path)
    else:
        save_report_html(report, out_path)

    click.echo(report.summary())
    if skipped:
        click.echo(f"Skipped {skipped} request(s) with no snapshot.")
