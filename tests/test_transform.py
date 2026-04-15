"""Tests for req_replay.transform module."""

import pytest
from datetime import datetime, timezone

from req_replay.models import CapturedRequest
from req_replay.transform import TransformConfig, transform_request


def _req(**kwargs) -> CapturedRequest:
    defaults = dict(
        id="test-id",
        timestamp=datetime.now(timezone.utc),
        method="GET",
        url="https://api.example.com/v1/users?page=1&limit=10",
        headers={"Authorization": "Bearer token123", "Accept": "application/json"},
        body=None,
        tags=[],
    )
    defaults.update(kwargs)
    return CapturedRequest(**defaults)


def test_no_transform_returns_equivalent_request():
    req = _req()
    result = transform_request(req, TransformConfig())
    assert result.url == req.url
    assert result.headers == req.headers
    assert result.body == req.body


def test_base_url_replaces_host():
    req = _req(url="https://api.example.com/v1/users")
    config = TransformConfig(base_url="https://staging.example.com")
    result = transform_request(req, config)
    assert result.url.startswith("https://staging.example.com")
    assert "/v1/users" in result.url


def test_base_url_preserves_path_and_query():
    req = _req(url="https://api.example.com/v1/items?sort=asc")
    config = TransformConfig(base_url="http://localhost:8080")
    result = transform_request(req, config)
    assert "localhost:8080" in result.url
    assert "/v1/items" in result.url
    assert "sort=asc" in result.url


def test_override_headers_adds_and_replaces():
    req = _req(headers={"Authorization": "Bearer old", "Accept": "application/json"})
    config = TransformConfig(override_headers={"Authorization": "Bearer new", "X-Custom": "yes"})
    result = transform_request(req, config)
    assert result.headers["Authorization"] == "Bearer new"
    assert result.headers["X-Custom"] == "yes"
    assert result.headers["Accept"] == "application/json"


def test_remove_headers_drops_keys():
    req = _req(headers={"Authorization": "Bearer token", "Accept": "*/*"})
    config = TransformConfig(remove_headers=["Authorization"])
    result = transform_request(req, config)
    assert "Authorization" not in result.headers
    assert "Accept" in result.headers


def test_remove_headers_case_insensitive():
    req = _req(headers={"authorization": "Bearer token"})
    config = TransformConfig(remove_headers=["Authorization"])
    result = transform_request(req, config)
    assert "authorization" not in result.headers


def test_override_query_params():
    req = _req(url="https://api.example.com/search?q=hello&page=1")
    config = TransformConfig(override_query_params={"page": "2"})
    result = transform_request(req, config)
    assert "page=2" in result.url
    assert "q=hello" in result.url


def test_remove_query_params():
    req = _req(url="https://api.example.com/items?debug=true&limit=5")
    config = TransformConfig(remove_query_params=["debug"])
    result = transform_request(req, config)
    assert "debug" not in result.url
    assert "limit=5" in result.url


def test_override_body():
    req = _req(body='{"old": true}', method="POST")
    config = TransformConfig(override_body='{"new": true}')
    result = transform_request(req, config)
    assert result.body == '{"new": true}'


def test_original_request_is_not_mutated():
    req = _req(headers={"Authorization": "Bearer original"})
    config = TransformConfig(override_headers={"Authorization": "Bearer changed"})
    transform_request(req, config)
    assert req.headers["Authorization"] == "Bearer original"
