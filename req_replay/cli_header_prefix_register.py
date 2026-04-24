"""Register the header-prefix CLI group."""
from req_replay.cli_header_prefix import header_prefix_group


def register(cli: object) -> None:  # type: ignore[type-arg]
    cli.add_command(header_prefix_group)  # type: ignore[attr-defined]
