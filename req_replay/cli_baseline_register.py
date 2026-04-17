"""Register baseline commands with the main CLI."""
from req_replay.cli_baseline import baseline_group


def register(cli: object) -> None:  # type: ignore[type-arg]
    """Attach baseline_group to the root CLI group."""
    cli.add_command(baseline_group)  # type: ignore[attr-defined]
