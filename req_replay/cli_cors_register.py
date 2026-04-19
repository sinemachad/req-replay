"""Register the cors CLI group."""
from req_replay.cli_cors import cors_group


def register(cli) -> None:  # type: ignore[type-arg]
    cli.add_command(cors_group, name="cors")
