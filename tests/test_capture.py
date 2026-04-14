"""Tests for the capture module."""

import pytest
from unittest.mock import MagicMock, patch

from req_replay.capture import capture_request, _build_captured_response
from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.storage import RequestStore


def _mock_response(status_code=200, text="OK", elapsed_ms=50.0):
    from datetime import timedelta
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {"Content-Type": "text/plain"}
    resp.text = text
    resp.elapsed = timedelta(milliseconds=elapsed_ms)
    return resp


@patch("req_replay.capture.requests.request")
def test_capture_returns_request_and_response(mock_req):
    mock_req.return_value = _mock_response(200, "Hello")
    req, resp = capture_request("GET", "http://example.com")

    assert req.method == "GET"
    assert req.url == "http://example.com"
    assert isinstance(req.id, str) and len(req.id) > 0
    assert resp.status_code == 200
    assert resp.body == "Hello"


@patch("req_replay.capture.requests.request")
def test_capture_stores_when_store_provided(mock_req, tmp_path):
    mock_req.return_value = _mock_response(201, "Created")
    store = RequestStore(str(tmp_path))

    req, resp = capture_request("POST", "http://example.com/items", store=store)

    loaded_req, loaded_resp = store.load(req.id)
    assert loaded_req.id == req.id
    assert loaded_resp.status_code == 201


@patch("req_replay.capture.requests.request")
def test_capture_with_tags(mock_req):
    mock_req.return_value = _mock_response()
    req, _ = capture_request("GET", "http://example.com", tags=["smoke", "auth"])
    assert "smoke" in req.tags
    assert "auth" in req.tags


@patch("req_replay.capture.requests.request")
def test_capture_does_not_store_without_store(mock_req, tmp_path):
    mock_req.return_value = _mock_response()
    req, _ = capture_request("GET", "http://example.com", store=None)
    store = RequestStore(str(tmp_path))
    assert req.id not in store.list_ids()


def test_build_captured_response_elapsed():
    from datetime import timedelta
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.headers = {}
    mock_resp.text = "Not Found"
    mock_resp.elapsed = timedelta(milliseconds=123)

    captured = _build_captured_response(mock_resp)
    assert captured.elapsed_ms == pytest.approx(123.0, rel=1e-3)
    assert captured.status_code == 404
