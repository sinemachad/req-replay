"""Tests for req_replay.schema."""
import json
import pytest
from req_replay.models import CapturedRequest
from req_replay.schema import validate_schema, SchemaResult


def _req(body: str | None = None, content_type: str = "application/json") -> CapturedRequest:
    headers = {"Content-Type": content_type} if content_type else {}
    return CapturedRequest(
        id="test-id",
        method="POST",
        url="https://example.com/api",
        headers=headers,
        body=body,
        timestamp="2024-01-01T00:00:00",
    )


def test_valid_body_no_warnings():
    schema = {"required": ["name"], "properties": {"name": {"type": "string"}}}
    req = _req(json.dumps({"name": "Alice"}))
    result = validate_schema(req, schema)
    assert result.passed()
    assert result.warnings == []


def test_missing_required_field_s003():
    schema = {"required": ["name", "age"]}
    req = _req(json.dumps({"name": "Alice"}))
    result = validate_schema(req, schema)
    assert not result.passed()
    codes = [w.code for w in result.warnings]
    assert "S003" in codes
    assert any("age" in w.message for w in result.warnings)


def test_wrong_type_s004():
    schema = {"properties": {"count": {"type": "integer"}}}
    req = _req(json.dumps({"count": "not-an-int"}))
    result = validate_schema(req, schema)
    assert not result.passed()
    assert result.warnings[0].code == "S004"


def test_no_json_content_type_with_required_s001():
    schema = {"required": ["name"]}
    req = _req(body="name=Alice", content_type="application/x-www-form-urlencoded")
    result = validate_schema(req, schema)
    assert not result.passed()
    assert result.warnings[0].code == "S001"


def test_no_json_content_type_no_required_passes():
    schema = {}
    req = _req(body="name=Alice", content_type="text/plain")
    result = validate_schema(req, schema)
    assert result.passed()


def test_body_not_object_s002():
    schema = {}
    req = _req(json.dumps([1, 2, 3]))
    result = validate_schema(req, schema)
    assert not result.passed()
    assert result.warnings[0].code == "S002"


def test_invalid_json_body_s001():
    schema = {"required": ["x"]}
    req = _req(body="{invalid json}")
    result = validate_schema(req, schema)
    assert not result.passed()
    assert result.warnings[0].code == "S001"


def test_summary_passed():
    schema = {}
    req = _req(json.dumps({"a": 1}))
    result = validate_schema(req, schema)
    assert "OK" in result.summary()


def test_summary_failed_contains_codes():
    schema = {"required": ["x", "y"]}
    req = _req(json.dumps({}))
    result = validate_schema(req, schema)
    assert "S003" in result.summary()


def test_empty_schema_valid_body_passes():
    schema = {}
    req = _req(json.dumps({"anything": True}))
    result = validate_schema(req, schema)
    assert result.passed()
