"""CLI commands for header hashing."""
from __future__ import annotations

import click

from req_replay.header_hash import batch_hash, compare_header_hashes, hash_headers
from req_replay.storage import RequestStore


@click.group("header-hash")
def header_hash_group() -> None:
    """Compute and compare stable hashes of request headers."""


@header_hash_group.command("show")
@click.argument("request_id")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option(
    "--algo",
    default="sha256",
    show_default=True,
    help="Hash algorithm: sha256, sha1, md5.",
)
def show_cmd(request_id: str, store_path: str, algo: str) -> None:
    """Show the header hash for a stored request."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Error: request '{request_id}' not found.", err=True)
        raise SystemExit(1)
    try:
        result = hash_headers(req, algorithm=algo)
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    click.echo(result.display())


@header_hash_group.command("compare")
@click.argument("id_a")
@click.argument("id_b")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option("--algo", default="sha256", show_default=True)
def compare_cmd(id_a: str, id_b: str, store_path: str, algo: str) -> None:
    """Compare header hashes of two stored requests."""
    store = RequestStore(store_path)
    for rid in (id_a, id_b):
        try:
            store.load(rid)
        except FileNotFoundError:
            click.echo(f"Error: request '{rid}' not found.", err=True)
            raise SystemExit(1)
    a, b = store.load(id_a), store.load(id_b)
    match = compare_header_hashes(a, b, algorithm=algo)
    status = "MATCH" if match else "DIFFER"
    click.echo(f"{id_a} vs {id_b}: {status}")


@header_hash_group.command("scan")
@click.option("--store", "store_path", default=".req_store", show_default=True)
@click.option("--algo", default="sha256", show_default=True)
def scan_cmd(store_path: str, algo: str) -> None:
    """Print header hashes for all stored requests."""
    store = RequestStore(store_path)
    requests = store.list()
    if not requests:
        click.echo("No requests found.")
        return
    results = batch_hash(requests, algorithm=algo)
    for r in results:
        click.echo(f"{r.request_id}  {r.algorithm}  {r.digest}  ({r.header_count} headers)")
