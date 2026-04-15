"""Export captured requests/responses to various formats (curl, HTTPie, HAR)."""
from __future__ import annotations

import json
from typing import Any

from req_replay.models import CapturedRequest, CapturedResponse


def to_curl(request: CapturedRequest) -> str:
    """Convert a CapturedRequest to a curl command string."""
    parts = ["curl", "-X", request.method]

    for key, value in request.headers.items():
        # Skip headers that curl sets automatically
        if key.lower() in ("content-length", "host"):
            continue
        parts.extend(["-H", f"{key!r}: {value!r}"])

    if request.body:
        body = request.body if isinstance(request.body, str) else request.body.decode()
        parts.extend(["--data", repr(body)])

    parts.append(repr(request.url))
    return " ".join(parts)


def to_httpie(request: CapturedRequest) -> str:
    """Convert a CapturedRequest to an HTTPie command string."""
    method = request.method.upper()
    parts = ["http", method, repr(request.url)]

    for key, value in request.headers.items():
        if key.lower() in ("content-length", "host"):
            continue
        parts.append(f"{key}:{value!r}")

    if request.body:
        body = request.body if isinstance(request.body, str) else request.body.decode()
        try:
            parsed = json.loads(body)
            for k, v in parsed.items():
                parts.append(f"{k}:={json.dumps(v)}")
        except (json.JSONDecodeError, AttributeError):
            parts.extend(["<<<", repr(body)])

    return " ".join(parts)


def to_har_entry(request: CapturedRequest, response: CapturedResponse | None = None) -> dict[str, Any]:
    """Build a HAR-format entry dict for a request/response pair."""
    body = request.body
    if isinstance(body, bytes):
        body = body.decode(errors="replace")

    har_request: dict[str, Any] = {
        "method": request.method,
        "url": request.url,
        "headers": [{"name": k, "value": v} for k, v in request.headers.items()],
        "queryString": [
            {"name": k, "value": v}
            for k, v in request.params.items()
        ],
        "postData": {"mimeType": request.headers.get("Content-Type", ""), "text": body or ""},
    }

    har_response: dict[str, Any] = {}
    if response is not None:
        resp_body = response.body
        if isinstance(resp_body, bytes):
            resp_body = resp_body.decode(errors="replace")
        har_response = {
            "status": response.status_code,
            "headers": [{"name": k, "value": v} for k, v in response.headers.items()],
            "content": {
                "mimeType": response.headers.get("Content-Type", ""),
                "text": resp_body or "",
            },
        }

    return {"request": har_request, "response": har_response}
