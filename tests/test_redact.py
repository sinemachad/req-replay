"""Tests for req_replay.redact."""

from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.redact import (
    RedactConfig,
    _REDACTED,
    redact_body,
    redact_headers,
    redact_query_params,
    redact_request,
    redact_response,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _req(**kwargs) -> CapturedRequest:
    defaults = dict(
        id="abc",
        timestamp="2024-01-01T00:00:00",
        method="GET",
        url="https://example.com/api",
        headers={"Authorization": "Bearer secret", "Content-Type": "application/json"},
        body=None,
        tags=[],
    )
    defaults.update(kwargs)
    return CapturedRequest(**defaults)


def _resp(**kwargs) -> CapturedResponse:
    defaults = dict(
        status_code=200,
        headers={"Set-Cookie": "session=abc123", "Content-Type": "application/json"},
        body='{"ok": true}',
        elapsed_ms=42.0,
    )
    defaults.update(kwargs)
    return CapturedResponse(**defaults)


# ---------------------------------------------------------------------------
# redact_headers
# ---------------------------------------------------------------------------

def test_redact_headers_replaces_sensitive():
    result = redact_headers({"Authorization": "Bearer tok", "Accept": "*/*"}, {"authorization"})
    assert result["Authorization"] == _REDACTED
    assert result["Accept"] == "*/*"


def test_redact_headers_case_insensitive_matching():
    result = redact_headers({"X-API-KEY": "mysecret"}, {"x-api-key"})
    assert result["X-API-KEY"] == _REDACTED


def test_redact_headers_empty_sensitive_set():
    headers = {"Authorization": "Bearer tok"}
    assert redact_headers(headers, set()) == headers


# ---------------------------------------------------------------------------
# redact_query_params
# ---------------------------------------------------------------------------

def test_redact_query_params_replaces_value():
    url = "https://example.com/search?q=hello&api_key=secret123"
    result = redact_query_params(url, ["api_key"])
    assert "secret123" not in result
    assert f"api_key={_REDACTED}" in result


def test_redact_query_params_no_sensitive_returns_url_unchanged():
    url = "https://example.com/?token=abc"
    assert redact_query_params(url, []) == url


def test_redact_query_params_multiple_params():
    url = "https://example.com/?token=abc&password=xyz&page=1"
    result = redact_query_params(url, ["token", "password"])
    assert "abc" not in result
    assert "xyz" not in result
    assert "page=1" in result


# ---------------------------------------------------------------------------
# redact_body
# ---------------------------------------------------------------------------

def test_redact_body_replaces_json_value():
    body = '{"username": "alice", "password": "s3cr3t"}'
    result = redact_body(body, ["password"])
    assert "s3cr3t" not in result
    assert f'"password": "{_REDACTED}"' in result
    assert '"username": "alice"' in result


def test_redact_body_none_returns_none():
    assert redact_body(None, ["password"]) is None


def test_redact_body_no_keys_returns_body_unchanged():
    body = '{"password": "s3cr3t"}'
    assert redact_body(body, []) == body


# ---------------------------------------------------------------------------
# redact_request / redact_response
# ---------------------------------------------------------------------------

def test_redact_request_redacts_auth_header():
    config = RedactConfig()
    result = redact_request(_req(), config)
    assert result.headers["Authorization"] == _REDACTED
    assert result.headers["Content-Type"] == "application/json"


def test_redact_request_preserves_metadata():
    req = _req(id="xyz", method="POST", tags=["smoke"])
    result = redact_request(req, RedactConfig())
    assert result.id == "xyz"
    assert result.method == "POST"
    assert result.tags == ["smoke"]


def test_redact_response_redacts_set_cookie():
    config = RedactConfig()
    result = redact_response(_resp(), config)
    assert result.headers["Set-Cookie"] == _REDACTED
    assert result.status_code == 200
