"""Register the header-coverage command group with the main CLI."""
from req_replay.cli_header_coverage import header_coverage_group


def register(cli: object) -> None:  # type: ignore[type-arg]
    cli.add_command(header_coverage_group)  # type: ignore[attr-defined]
