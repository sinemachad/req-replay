"""Register the anomaly CLI group."""
from req_replay.cli_anomaly import anomaly_group


def register(cli) -> None:  # noqa: ANN001
    """Register the anomaly command group with the root CLI.

    Args:
        cli: The root Click group to attach the anomaly subgroup to.
    """
    cli.add_command(anomaly_group, name="anomaly")
