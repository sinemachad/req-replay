"""CLI commands for TLS inspection."""
from __future__ import annotations

import click
from req_replay.tls import inspect_tls


@click.group("tls")
def tls_group():
    """Inspect TLS/SSL certificates for request URLs."""


@tls_group.command("inspect")
@click.argument("url")
@click.option("--timeout", default=5.0, show_default=True, help="Connection timeout in seconds.")
def inspect_cmd(url: str, timeout: float):
    """Inspect the TLS certificate for URL."""
    try:
        info = inspect_tls(url, timeout=timeout)
        click.echo(info.display())
        days = info.days_until_expiry()
        if days is not None and days < 30:
            click.secho(f"\nWarning: certificate expires in {days} day(s).", fg="yellow")
        if info.expired():
            click.secho("\nError: certificate has expired!", fg="red")
    except Exception as exc:  # noqa: BLE001
        click.secho(f"Failed to inspect TLS for {url}: {exc}", fg="red", err=True)
        raise SystemExit(1) from exc


@tls_group.command("check")
@click.argument("url")
@click.option("--warn-days", default=30, show_default=True, help="Warn if expiry within N days.")
def check_cmd(url: str, warn_days: int):
    """Exit non-zero if certificate is expired or expiring soon."""
    try:
        info = inspect_tls(url)
    except Exception as exc:  # noqa: BLE001
        click.secho(f"TLS check failed: {exc}", fg="red", err=True)
        raise SystemExit(2) from exc

    if info.expired():
        click.secho("FAIL: certificate expired.", fg="red")
        raise SystemExit(1)

    days = info.days_until_expiry()
    if days is not None and days < warn_days:
        click.secho(f"WARN: certificate expires in {days} day(s).", fg="yellow")
        raise SystemExit(1)

    click.secho("OK: certificate is valid.", fg="green")
