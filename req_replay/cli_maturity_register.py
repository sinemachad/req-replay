"""Registration shim so cli.py can add the maturity command group."""
from req_replay.cli_maturity import maturity_group


def register(cli) -> None:  # pragma: no cover
    cli.add_command(maturity_group, name="maturity")
