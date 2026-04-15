"""CLI commands for managing and running assertion rules."""
from __future__ import annotations

import json
from pathlib import Path

import click

from req_replay.assert_config import load_rules, save_rules, rules_from_dict
from req_replay.assert_rules import evaluate_rules
from req_replay.storage import RequestStore


@click.group("assert")
def assert_group():
    """Manage and run assertion rules against captured responses."""


@assert_group.command("run")
@click.argument("request_id")
@click.option("--rules", "rules_path", required=True, type=click.Path(), help="Path to rules JSON file.")
@click.option("--store", "store_dir", default=".req_replay", show_default=True, help="Storage directory.")
def run_assert(request_id: str, rules_path: str, store_dir: str) -> None:
    """Run assertion rules against a stored response."""
    store = RequestStore(Path(store_dir))
    try:
        req, resp = store.load(request_id)
    except FileNotFoundError:
        raise click.ClickException(f"Request '{request_id}' not found.")

    try:
        rules = load_rules(Path(rules_path))
    except (FileNotFoundError, ValueError) as exc:
        raise click.ClickException(str(exc))

    results = evaluate_rules(resp, rules)
    all_passed = all(r.passed for r in results)

    for result in results:
        color = "green" if result.passed else "red"
        click.echo(click.style(str(result), fg=color))

    if all_passed:
        click.echo(click.style("\nAll assertions passed.", fg="green", bold=True))
    else:
        failed = sum(1 for r in results if not r.passed)
        click.echo(click.style(f"\n{failed}/{len(results)} assertion(s) failed.", fg="red", bold=True))
        raise SystemExit(1)


@assert_group.command("init")
@click.argument("output", default="assertions.json")
def init_rules(output: str) -> None:
    """Create a starter assertion rules file."""
    starter = [
        {"field": "status", "operator": "eq", "expected": 200},
        {"field": "body_contains", "operator": "contains", "expected": ""},
    ]
    path = Path(output)
    if path.exists():
        raise click.ClickException(f"{output} already exists.")
    path.write_text(json.dumps(starter, indent=2))
    click.echo(f"Created {output}")
