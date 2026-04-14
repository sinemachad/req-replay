"""Tests for the replay module."""

import pytest
from unittest.mock import patch

from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.replay import ReplayResult, replay_request
from req_replay.storage import RequestStore


def _make_response(status=200, body="OK"):
    return CapturedResponse(status_code=status, headers={}, body=body, elapsed_ms=10.0)


def _make_request(rid="abc", url="http://example.com"):
    return CapturedRequest(
        id=rid, method="GET", url=url,
        headers={}, body=None, timestamp=0.0, tags=[]
    )


def test_replay_result_pass():
    orig = _make_response(200, "Hello")
    replayed = _make_response(200, "Hello")
    result = ReplayResult(request_id="1", original_response=orig, replayed_response=replayed)
    assert result.passed is True
    assert "PASS" in result.summary()


def test_replay_result_fail_status():
    orig = _make_response(200, "Hello")
    replayed = _make_response(500, "Hello")
    result = ReplayResult(request_id="1", original_response=orig, replayed_response=replayed)
    assert result.passed is False
    assert result.status_match is False


def test_replay_result_fail_body():
    orig = _make_response(200, "Hello")
    replayed = _make_response(200, "World")
    result = ReplayResult(request_id="1", original_response=orig, replayed_response=replayed)
    assert result.passed is False
    assert result.body_match is False


@patch("req_replay.replay._send_request")
def test_replay_request_uses_stored_data(mock_send, tmp_path):
    from datetime import timedelta
    mock_resp = _mock_http_response(200, "Stored Body")
    mock_send.return_value = mock_resp

    store = RequestStore(str(tmp_path))
    req = _make_request(rid="test-id")
    orig_resp = _make_response(200, "Stored Body")
    store.save(req, orig_resp)

    result = replay_request("test-id", store)
    assert result.request_id == "test-id"
    assert result.passed is True


@patch("req_replay.replay._send_request")
def test_replay_request_override_url(mock_send, tmp_path):
    mock_send.return_value = _mock_http_response(200, "OK")
    store = RequestStore(str(tmp_path))
    req = _make_request(rid="url-test", url="http://original.com")
    store.save(req, _make_response(200, "OK"))

    replay_request("url-test", store, override_url="http://override.com")
    called_req = mock_send.call_args[0][0]
    assert called_req.url == "http://override.com"


def _mock_http_response(status_code=200, text="OK"):
    from unittest.mock import MagicMock
    from datetime import timedelta
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {}
    resp.text = text
    resp.elapsed = timedelta(milliseconds=10)
    return resp
