"""Tests for req_replay.header_template."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from req_replay.header_template import (
    TemplateResult,
    render_headers,
    render_request_headers,
)
from req_replay.models import CapturedRequest


def _req(**kwargs) -> CapturedRequest:
    defaults = dict(
        id="req-1",
        method="GET",
        url="https://example.com/api",
        headers={"Authorization": "Bearer {{token}}", "X-Tenant": "{{tenant}}"},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )
    defaults.update(kwargs)
    return CapturedRequest(**defaults)


def test_render_replaces_single_variable():
    result = render_headers({"Authorization": "Bearer {{token}}"}, {"token": "abc123"})
    assert result.rendered["Authorization"] == "Bearer abc123"


def test_render_replaces_multiple_variables():
    headers = {"Authorization": "Bearer {{token}}", "X-Tenant": "{{tenant}}"}
    result = render_headers(headers, {"token": "t1", "tenant": "acme"})
    assert result.rendered["Authorization"] == "Bearer t1"
    assert result.rendered["X-Tenant"] == "acme"


def test_render_leaves_unknown_placeholder_intact():
    result = render_headers({"X-Custom": "{{unknown}}"}, {})
    assert result.rendered["X-Custom"] == "{{unknown}}"


def test_render_changed_is_true_when_substitution_made():
    result = render_headers({"X-Key": "{{val}}"}, {"val": "replaced"})
    assert result.changed is True


def test_render_changed_is_false_when_no_substitution():
    result = render_headers({"X-Key": "static"}, {"val": "replaced"})
    assert result.changed is False


def test_substitutions_list_contains_changed_keys():
    result = render_headers(
        {"A": "{{x}}", "B": "static"},
        {"x": "v"},
    )
    assert "A" in result.substitutions
    assert "B" not in result.substitutions


def test_display_shows_before_and_after():
    result = render_headers({"Authorization": "Bearer {{tok}}"}, {"tok": "secret"})
    display = result.display()
    assert "Authorization" in display
    assert "secret" in display


def test_display_no_changes_message():
    result = render_headers({"X-Static": "value"}, {})
    assert "No substitutions" in result.display()


def test_original_is_not_mutated():
    headers = {"X-Key": "{{var}}"}
    render_headers(headers, {"var": "new"})
    assert headers["X-Key"] == "{{var}}"


def test_render_request_headers_returns_new_request():
    req = _req()
    updated = render_request_headers(req, {"token": "mytoken", "tenant": "corp"})
    assert updated.headers["Authorization"] == "Bearer mytoken"
    assert updated.headers["X-Tenant"] == "corp"
    # original unchanged
    assert req.headers["Authorization"] == "Bearer {{token}}"


def test_render_request_headers_preserves_other_fields():
    req = _req(tags=["smoke"], metadata={"env": "prod"})
    updated = render_request_headers(req, {})
    assert updated.id == req.id
    assert updated.method == req.method
    assert updated.url == req.url
    assert updated.tags == ["smoke"]
    assert updated.metadata == {"env": "prod"}


def test_empty_variables_returns_unchanged_headers():
    headers = {"X-Api-Key": "hardcoded"}
    result = render_headers(headers, {})
    assert result.rendered == headers
    assert not result.changed
