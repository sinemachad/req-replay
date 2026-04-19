"""Register the boundary CLI group."""
from req_replay.cli_boundary import boundary_group


def register(cli) -> None:  # noqa: ANN001
    cli.add_command(boundary_group)
