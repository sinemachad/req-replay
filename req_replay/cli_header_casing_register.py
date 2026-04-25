"""Register the header-casing command group with the main CLI."""
from req_replay.cli_header_casing import header_casing_group


def register(cli: object) -> None:  # type: ignore[type-arg]
    cli.add_command(header_casing_group)  # type: ignore[attr-defined]
