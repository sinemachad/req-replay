"""CLI commands for latency analysis."""
from __future__ import annotations

from pathlib import Path

import click

from req_replay.storage import RequestStore
from req_replay.filter import FilterCriteria, filter_requests
from req_replay.latency import analyze_latency


@click.group("latency")
def latency_group() -> None:
    """Analyse request latency from stored duration_ms metadata."""


@latency_group.command("stats")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
@click.option("--method", default=None, help="Filter by HTTP method.")
@click.option("--url", "url_pattern", default=None, help="URL substring filter.")
@click.option("--tag", default=None, help="Filter by tag.")
def stats_cmd(
    store_path: str,
    method: str | None,
    url_pattern: str | None,
    tag: str | None,
) -> None:
    """Print latency statistics for matching requests."""
    store = RequestStore(Path(store_path))
    requests = store.list()
    criteria = FilterCriteria(method=method, url_pattern=url_pattern, tag=tag)
    requests = filter_requests(requests, criteria)
    result = analyze_latency(requests)
    if result is None:
        click.echo("No duration_ms metadata found in matching requests.")
        return
    click.echo(result.display())


@latency_group.command("histogram")
@click.option("--store", "store_path", default=".req_replay", show_default=True)
@click.option("--buckets", default=5, show_default=True, help="Number of histogram buckets.")
def histogram_cmd(store_path: str, buckets: int) -> None:
    """Print a simple ASCII histogram of request latencies."""
    store = RequestStore(Path(store_path))
    requests = store.list()
    result = analyze_latency(requests)
    if result is None:
        click.echo("No duration_ms metadata found.")
        return
    s = result.samples
    width = (result.max_ms - result.min_ms) or 1.0
    bucket_size = width / buckets
    counts = [0] * buckets
    for v in s:
        idx = min(int((v - result.min_ms) / bucket_size), buckets - 1)
        counts[idx] += 1
    max_count = max(counts) or 1
    bar_width = 30
    for i, c in enumerate(counts):
        lo = result.min_ms + i * bucket_size
        hi = lo + bucket_size
        bar = "#" * int(c / max_count * bar_width)
        click.echo(f"{lo:7.1f}-{hi:7.1f} ms | {bar:<{bar_width}} {c}")
