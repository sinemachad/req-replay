"""Register the header-merge command group with the main CLI."""
from req_replay.cli_header_merge import header_merge_group


def register(cli: object) -> None:  # type: ignore[type-arg]
    cli.add_command(header_merge_group)  # type: ignore[attr-defined]
