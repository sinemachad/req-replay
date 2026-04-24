"""Register the header-expiry command group with the root CLI."""
from req_replay.cli_header_expiry import header_expiry_group


def register(cli: object) -> None:  # type: ignore[type-arg]
    cli.add_command(header_expiry_group)  # type: ignore[attr-defined]
