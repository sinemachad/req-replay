"""Schema validation for captured request bodies."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from req_replay.models import CapturedRequest


@dataclass
class SchemaWarning:
    code: str
    message: str

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message}


@dataclass
class SchemaResult:
    request_id: str
    warnings: list[SchemaWarning] = field(default_factory=list)

    def passed(self) -> bool:
        return len(self.warnings) == 0

    def summary(self) -> str:
        if self.passed():
            return f"{self.request_id}: schema OK"
        codes = ", ".join(w.code for w in self.warnings)
        return f"{self.request_id}: schema issues [{codes}]"


def _get_json_body(request: CapturedRequest) -> Any | None:
    import json
    ct = ""
    for k, v in (request.headers or {}).items():
        if k.lower() == "content-type":
            ct = v
            break
    if "application/json" not in ct:
        return None
    try:
        return json.loads(request.body or "")
    except (ValueError, TypeError):
        return None


def validate_schema(request: CapturedRequest, schema: dict) -> SchemaResult:
    """Validate request body against a JSON Schema (subset: required + type)."""
    warnings: list[SchemaWarning] = []
    body = _get_json_body(request)

    if body is None:
        if schema.get("required"):
            warnings.append(SchemaWarning("S001", "Expected JSON body but none found or content-type missing"))
        return SchemaResult(request_id=request.id, warnings=warnings)

    if not isinstance(body, dict):
        warnings.append(SchemaWarning("S002", "Request body is not a JSON object"))
        return SchemaResult(request_id=request.id, warnings=warnings)

    for key in schema.get("required", []):
        if key not in body:
            warnings.append(SchemaWarning("S003", f"Missing required field: '{key}'"))

    for prop, prop_schema in schema.get("properties", {}).items():
        if prop not in body:
            continue
        expected_type = prop_schema.get("type")
        if expected_type is None:
            continue
        type_map = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "array": list, "object": dict}
        py_type = type_map.get(expected_type)
        if py_type and not isinstance(body[prop], py_type):
            warnings.append(SchemaWarning("S004", f"Field '{prop}' expected type '{expected_type}'"))

    return SchemaResult(request_id=request.id, warnings=warnings)
