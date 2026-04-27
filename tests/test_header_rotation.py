"""Tests for req_replay.header_rotation."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from req_replay.header_rotation import RotationConfig, RotationResult, rotate_headers
from req_replay.models import CapturedRequest


def _req(headers: dict | None = None) -> CapturedRequest:
    return CapturedRequest(
        id="req-1",
        method="GET",
        url="https://example.com/api",
        headers=headers or {},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


# ---------------------------------------------------------------------------
# RotationConfig.next_index
# ---------------------------------------------------------------------------

def test_next_index_cycles_through_values():
    config = RotationConfig(values={"x-env": ["dev", "staging", "prod"]})
    assert config.next_index("x-env") == 0
    assert config.next_index("x-env") == 1
    assert config.next_index("x-env") == 2
    assert config.next_index("x-env") == 0  # wraps


def test_next_index_empty_pool_returns_zero():
    config = RotationConfig(values={})
    assert config.next_index("x-missing") == 0


def test_reset_single_header():
    config = RotationConfig(values={"x-env": ["a", "b"]})
    config.next_index("x-env")
    config.next_index("x-env")
    config.reset("x-env")
    assert config.next_index("x-env") == 0


def test_reset_all_headers():
    config = RotationConfig(values={"x-a": ["1", "2"], "x-b": ["p", "q"]})
    config.next_index("x-a")
    config.next_index("x-b")
    config.reset()
    assert config.next_index("x-a") == 0
    assert config.next_index("x-b") == 0


# ---------------------------------------------------------------------------
# rotate_headers
# ---------------------------------------------------------------------------

def test_rotate_headers_replaces_value():
    req = _req({"x-env": "dev"})
    config = RotationConfig(values={"x-env": ["staging", "prod"]})
    new_req, results = rotate_headers(req, config)
    assert new_req.headers["x-env"] == "staging"
    assert len(results) == 1
    assert results[0].changed is True
    assert results[0].old_value == "dev"
    assert results[0].new_value == "staging"


def test_rotate_headers_adds_missing_header():
    req = _req({})
    config = RotationConfig(values={"x-token": ["abc", "xyz"]})
    new_req, results = rotate_headers(req, config)
    assert new_req.headers["x-token"] == "abc"
    assert results[0].old_value is None
    assert results[0].changed is True


def test_rotate_headers_unchanged_when_value_same():
    req = _req({"x-env": "dev"})
    config = RotationConfig(values={"x-env": ["dev"]})
    _, results = rotate_headers(req, config)
    assert results[0].changed is False


def test_rotate_headers_does_not_mutate_original():
    req = _req({"x-env": "dev"})
    config = RotationConfig(values={"x-env": ["prod"]})
    rotate_headers(req, config)
    assert req.headers["x-env"] == "dev"


def test_rotate_headers_empty_config_returns_same_headers():
    req = _req({"x-env": "dev"})
    config = RotationConfig(values={})
    new_req, results = rotate_headers(req, config)
    assert new_req.headers == {"x-env": "dev"}
    assert results == []


# ---------------------------------------------------------------------------
# RotationResult.display
# ---------------------------------------------------------------------------

def test_rotation_result_display_changed():
    r = RotationResult(
        request_id="r1", header="x-env",
        old_value="dev", new_value="prod",
        index=1, changed=True,
    )
    assert "changed" in r.display()
    assert "x-env" in r.display()


def test_rotation_result_display_unchanged():
    r = RotationResult(
        request_id="r1", header="x-env",
        old_value="dev", new_value="dev",
        index=0, changed=False,
    )
    assert "unchanged" in r.display()
