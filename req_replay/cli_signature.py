"""CLI commands for request signing and verification."""
import click

from req_replay.signature import sign_request, verify_request
from req_replay.storage import RequestStore


@click.group("signature")
def signature_group() -> None:
    """Sign and verify captured requests."""


@signature_group.command("sign")
@click.argument("request_id")
@click.option("--secret", required=True, envvar="RR_SIGN_SECRET", help="HMAC secret key")
@click.option("--algorithm", default="sha256", show_default=True, help="sha256 or sha512")
@click.option("--store", "store_path", default=".req_store", show_default=True)
def sign_cmd(request_id: str, secret: str, algorithm: str, store_path: str) -> None:
    """Generate an HMAC signature for a stored request."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)
    try:
        result = sign_request(req, secret, algorithm)
    except ValueError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)
    click.echo(result.display())


@signature_group.command("verify")
@click.argument("request_id")
@click.option("--secret", required=True, envvar="RR_SIGN_SECRET")
@click.option("--signature", "expected_sig", required=True, help="Expected hex signature")
@click.option("--algorithm", default="sha256", show_default=True)
@click.option("--store", "store_path", default=".req_store", show_default=True)
def verify_cmd(
    request_id: str, secret: str, expected_sig: str, algorithm: str, store_path: str
) -> None:
    """Verify a signature against a stored request."""
    store = RequestStore(store_path)
    try:
        req = store.load(request_id)
    except FileNotFoundError:
        click.echo(f"Request '{request_id}' not found.", err=True)
        raise SystemExit(1)
    result = verify_request(req, secret, expected_sig, algorithm)
    click.echo(result.display())
    if not result.verified:
        raise SystemExit(1)
