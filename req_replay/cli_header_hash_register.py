"""Register the header-hash command group with the main CLI."""
from req_replay.cli_header_hash import header_hash_group


def register(cli) -> None:  # noqa: ANN001
    cli.add_command(header_hash_group)
