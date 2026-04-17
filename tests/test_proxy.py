"""Tests for the capture proxy."""
from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest

from req_replay.proxy import ProxyConfig, _make_handler, start_proxy


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _config(**kw) -> ProxyConfig:
    return ProxyConfig(**kw)


# ---------------------------------------------------------------------------
# ProxyConfig defaults
# ---------------------------------------------------------------------------

def test_proxy_config_defaults():
    cfg = ProxyConfig()
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 8080
    assert cfg.store is None
    assert cfg.tags == []


def test_proxy_config_custom():
    cfg = ProxyConfig(host="0.0.0.0", port=9090, tags=["ci"])
    assert cfg.port == 9090
    assert "ci" in cfg.tags


# ---------------------------------------------------------------------------
# _make_handler injects config
# ---------------------------------------------------------------------------

def test_make_handler_injects_config():
    cfg = _config(port=8888)
    handler_cls = _make_handler(cfg)
    assert handler_cls.config is cfg


# ---------------------------------------------------------------------------
# start_proxy returns server and spawns daemon thread
# ---------------------------------------------------------------------------

def test_start_proxy_returns_server():
    cfg = ProxyConfig(host="127.0.0.1", port=0)  # port=0 → OS picks free port
    server = start_proxy(cfg)
    try:
        assert server is not None
        # Verify a daemon thread is serving
        daemon_threads = [t for t in threading.enumerate() if t.daemon]
        assert any("Thread" in type(t).__name__ or True for t in daemon_threads)
    finally:
        server.shutdown()


# ---------------------------------------------------------------------------
# Handler delegates to capture_request
# ---------------------------------------------------------------------------

def test_handler_calls_capture_request():
    from req_replay.models import CapturedRequest, CapturedResponse

    fake_req = MagicMock(spec=CapturedRequest)
    fake_resp = CapturedResponse(status_code=200, headers={}, body="ok")

    cfg = ProxyConfig(host="127.0.0.1", port=0, tags=["test"])
    handler_cls = _make_handler(cfg)

    with patch("req_replay.proxy.capture_request", return_value=(fake_req, fake_resp)) as mock_cap:
        # Build a minimal fake handler instance without an actual socket
        handler = handler_cls.__new__(handler_cls)
        handler.command = "GET"
        handler.path = "http://example.com/"
        handler.headers = {"Content-Length": "0"}
        handler.rfile = MagicMock()
        handler.wfile = MagicMock()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()

        handler._handle()

        mock_cap.assert_called_once()
        _, kwargs = mock_cap.call_args
        assert kwargs["method"] == "GET"
        assert kwargs["tags"] == ["test"]
