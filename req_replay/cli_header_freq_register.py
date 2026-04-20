"""Register header-freq commands with the main CLI."""
from req_replay.cli_header_freq import header_freq_group


def register(cli) -> None:  # noqa: ANN001
    cli.add_command(header_freq_group)
