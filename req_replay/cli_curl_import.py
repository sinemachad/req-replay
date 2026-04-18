"""CLI commands for importing curl commands as captured requests."""
from __future__ import annotations

import sys

import click

from req_replay.curl_import import CurlParseError, parse_curl
from req_replay.storage import RequestStore


@click.group("curl-import")
def curl_import_group() -> None:
    """Import curl commands as captured requests."""


@curl_import_group.command("add")
@click.argument("store_path", envvar="RR_STORE")
@click.option("--command", "-c", default=None, help="curl command string")
@click.option("--file", "-f", "cmd_file", default=None, type=click.Path(exists=True),
              help="File containing one curl command per line")
@click.option("--tag", "-t", multiple=True, help="Tags to attach to imported requests")
def add_cmd(store_path: str, command: str | None, cmd_file: str | None, tag: tuple[str, ...]) -> None:
    """Import one or more curl commands into the store."""
    store = RequestStore(store_path)

    commands: list[str] = []
    if command:
        commands.append(command)
    if cmd_file:
        with open(cmd_file) as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    commands.append(line)

    if not commands:
        click.echo("No commands provided. Use --command or --file.", err=True)
        sys.exit(1)

    imported = 0
    for cmd in commands:
        try:
            req = parse_curl(cmd)
            if tag:
                req.tags = sorted(set(req.tags) | set(tag))
            store.save(req)
            click.echo(f"Imported {req.method} {req.url} → {req.id}")
            imported += 1
        except CurlParseError as exc:
            click.echo(f"[skip] {exc}", err=True)

    click.echo(f"\n{imported}/{len(commands)} command(s) imported.")
