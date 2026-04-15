"""Utilities for redacting sensitive data from captured requests and responses."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

from req_replay.models import CapturedRequest, CapturedResponse

_REDACTED = "**REDACTED**"

DEFAULT_SENSITIVE_HEADERS = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-auth-token",
}


@dataclass
class RedactConfig:
    """Configuration controlling which fields are redacted."""

    sensitive_headers: set = field(default_factory=lambda: set(DEFAULT_SENSITIVE_HEADERS))
    sensitive_query_params: List[str] = field(default_factory=list)
    sensitive_body_keys: List[str] = field(default_factory=list)


def redact_headers(headers: Dict[str, str], sensitive: set) -> Dict[str, str]:
    """Return a copy of *headers* with sensitive values replaced."""
    return {
        k: (_REDACTED if k.lower() in sensitive else v)
        for k, v in headers.items()
    }


def redact_query_params(url: str, sensitive_params: List[str]) -> str:
    """Replace values of sensitive query parameters in *url*."""
    if not sensitive_params:
        return url
    pattern = "|".join(re.escape(p) for p in sensitive_params)
    return re.sub(
        rf"({pattern})=([^&]*)",
        lambda m: f"{m.group(1)}={_REDACTED}",
        url,
        flags=re.IGNORECASE,
    )


def redact_body(body: str | None, sensitive_keys: List[str]) -> str | None:
    """Replace values of sensitive keys in a JSON-like body string."""
    if not body or not sensitive_keys:
        return body
    for key in sensitive_keys:
        body = re.sub(
            rf'("{re.escape(key)}"\s*:\s*)"[^"]*"',
            rf'\1"{_REDACTED}"',
            body,
        )
    return body


def redact_request(req: CapturedRequest, config: RedactConfig) -> CapturedRequest:
    """Return a new *CapturedRequest* with sensitive data redacted."""
    return CapturedRequest(
        id=req.id,
        timestamp=req.timestamp,
        method=req.method,
        url=redact_query_params(req.url, config.sensitive_query_params),
        headers=redact_headers(req.headers, config.sensitive_headers),
        body=redact_body(req.body, config.sensitive_body_keys),
        tags=req.tags,
    )


def redact_response(resp: CapturedResponse, config: RedactConfig) -> CapturedResponse:
    """Return a new *CapturedResponse* with sensitive headers redacted."""
    return CapturedResponse(
        status_code=resp.status_code,
        headers=redact_headers(resp.headers, config.sensitive_headers),
        body=resp.body,
        elapsed_ms=resp.elapsed_ms,
    )
