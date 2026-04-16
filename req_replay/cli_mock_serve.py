"""Lightweight HTTP mock server using wsgiref."""
from __future__ import annotations

import json
from pathlib import Path
from wsgiref.simple_server import make_server

import click

from req_replay.mock import MockRule, MockServer


def _load_server(rules_file: str) -> MockServer:
    data = json.loads(Path(rules_file).read_text())
    server = MockServer()
    for d in data:
        server.add_rule(MockRule.from_dict(d))
    return server


def _make_wsgi_app(mock: MockServer):
    def app(environ, start_response):
        method = environ["REQUEST_METHOD"]
        path = environ.get("PATH_INFO", "/")
        response = mock.match(method, path)
        if response is None:
            start_response("404 Not Found", [("Content-Type", "text/plain")])
            return [b"No mock rule matched."]
        status_line = f"{response.status_code} MOCK"
        headers = [(k, v) for k, v in response.headers.items()]
        if not any(k.lower() == "content-type" for k, _ in headers):
            headers.append(("Content-Type", "text/plain"))
        start_response(status_line, headers)
        body = (response.body or "").encode()
        return [body]
    return app


@click.command("serve")
@click.argument("rules_file", type=click.Path(exists=True))
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=9090, show_default=True, type=int)
def serve_cmd(rules_file: str, host: str, port: int) -> None:
    """Start a mock HTTP server from a rules file."""
    mock = _load_server(rules_file)
    click.echo(f"Mock server running on http://{host}:{port} with {mock.rule_count()} rule(s). Ctrl+C to stop.")
    httpd = make_server(host, port, _make_wsgi_app(mock))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        click.echo("\nStopped.")
