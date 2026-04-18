"""CLI commands for request tracing."""
from __future__ import annotations

import json
from pathlib import Path

import click

from req_replay.storage import RequestStore
from req_replay.trace import RequestTrace, TraceSpan, build_trace


@click.group("trace")
def trace_group() -> None:
    """Manage request trace spans."""


@trace_group.command("show")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
def show_cmd(request_id: str, store_path: str) -> None:
    """Display trace spans attached to a request."""
    store = RequestStore(Path(store_path))
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request {request_id!r} not found.", err=True)
        raise SystemExit(1)

    raw_spans = req.metadata.get("trace_spans", [])
    if not raw_spans:
        click.echo("No trace spans recorded for this request.")
        return

    trace = build_trace(request_id, raw_spans)
    click.echo(trace.display())


@trace_group.command("add")
@click.argument("request_id")
@click.argument("span_name")
@click.argument("duration_ms", type=float)
@click.option("--meta", multiple=True, help="key=value metadata pairs")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
def add_cmd(
    request_id: str,
    span_name: str,
    duration_ms: float,
    meta: tuple[str, ...],
    store_path: str,
) -> None:
    """Attach a span to an existing request."""
    store = RequestStore(Path(store_path))
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request {request_id!r} not found.", err=True)
        raise SystemExit(1)

    metadata: dict = {}
    for pair in meta:
        if "=" in pair:
            k, v = pair.split("=", 1)
            metadata[k] = v

    trace = build_trace(request_id, req.metadata.get("trace_spans", []))
    from req_replay.trace import record_span, _now_iso
    span = record_span(trace, span_name, duration_ms, metadata)

    spans_raw = [s.to_dict() for s in trace.spans]
    req.metadata["trace_spans"] = spans_raw
    store.save(req)
    click.echo(f"Span '{span_name}' ({duration_ms} ms) added to {request_id}.")
