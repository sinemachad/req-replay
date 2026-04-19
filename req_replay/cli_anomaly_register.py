"""Register the anomaly CLI group."""
from req_replay.cli_anomaly import anomaly_group


def register(cli) -> None:  # noqa: ANN001
    cli.add_command(anomaly_group, name="anomaly")
