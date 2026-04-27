"""Register header-deprecation CLI group."""
from req_replay.cli_header_deprecation import header_deprecation_group


def register(cli: object) -> None:  # type: ignore[type-arg]
    cli.add_command(header_deprecation_group)  # type: ignore[attr-defined]
