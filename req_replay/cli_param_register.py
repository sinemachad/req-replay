"""Registration helper to attach param_group to the main CLI."""
from req_replay.cli_param import param_group


def register(cli) -> None:  # pragma: no cover
    """Attach the param command group to a Click CLI app."""
    cli.add_command(param_group, name="param")
