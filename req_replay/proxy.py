"""Transparent HTTP proxy that auto-captures requests into a store."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

from req_replay.capture import capture_request
from req_replay.storage import RequestStore


@dataclass
class ProxyConfig:
    host: str = "127.0.0.1"
    port: int = 8080
    store: Optional[RequestStore] = None
    tags: list[str] = field(default_factory=list)


class _ProxyHandler(BaseHTTPRequestHandler):
    config: ProxyConfig  # injected by factory

    def _handle(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8", errors="replace") if length else None

        target = self.headers.get("X-Forwarded-For-URL") or self.path
        headers = {k: v for k, v in self.headers.items()}

        try:
            _req, resp = capture_request(
                method=self.command,
                url=target,
                headers=headers,
                body=body,
                store=self.config.store,
                tags=self.config.tags,
            )
        except Exception as exc:  # noqa: BLE001
            self.send_error(502, str(exc))
            return

        self.send_response(resp.status_code)
        for k, v in resp.headers.items():
            self.send_header(k, v)
        self.end_headers()
        if resp.body:
            self.wfile.write(resp.body.encode())

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = do_HEAD = _handle

    def log_message(self, fmt: str, *args: object) -> None:  # silence default logging
        pass


def _make_handler(config: ProxyConfig) -> type:
    return type("BoundHandler", (_ProxyHandler,), {"config": config})


def start_proxy(config: ProxyConfig) -> HTTPServer:
    """Start proxy server in a daemon thread; returns the server instance."""
    server = HTTPServer((config.host, config.port), _make_handler(config))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
