"""Register header-whitelist commands with the main CLI."""
from req_replay.cli_header_whitelist import header_whitelist_group


def register(cli: object) -> None:  # type: ignore[type-arg]
    cli.add_command(header_whitelist_group)  # type: ignore[union-attr]
