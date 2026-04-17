"""CLI commands for the capture proxy."""
from __future__ import annotations

import signal
import sys

import click

from req_replay.proxy import ProxyConfig, start_proxy
from req_replay.storage import RequestStore


@click.group("proxy")
def proxy_group() -> None:
    """Run a local HTTP proxy that captures requests."""


@proxy_group.command("start")
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8080, show_default=True, type=int)
@click.option("--store", "store_path", default=".req_replay", show_default=True)
@click.option("--tag", "tags", multiple=True, help="Tags to attach to captured requests.")
def start_cmd(host: str, port: int, store_path: str, tags: tuple[str, ...]) -> None:
    """Start the capture proxy and block until interrupted."""
    store = RequestStore(store_path)
    config = ProxyConfig(host=host, port=port, store=store, tags=list(tags))
    server = start_proxy(config)
    click.echo(f"Proxy listening on {host}:{port}  (store: {store_path})")
    click.echo("Press Ctrl+C to stop.")

    def _shutdown(sig: int, frame: object) -> None:  # noqa: ARG001
        click.echo("\nShutting down proxy...")
        server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)
    server.serve_forever()
