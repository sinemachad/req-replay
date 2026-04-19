"""CORS header analysis for captured request/response pairs."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from req_replay.models import CapturedRequest, CapturedResponse

_CORS_RESPONSE_HEADERS = {
    "access-control-allow-origin",
    "access-control-allow-methods",
    "access-control-allow-headers",
    "access-control-allow-credentials",
    "access-control-max-age",
    "access-control-expose-headers",
}


@dataclass
class CORSInfo:
    is_cors_request: bool
    origin: Optional[str]
    allow_origin: Optional[str]
    allow_methods: Optional[str]
    allow_headers: Optional[str]
    allow_credentials: bool
    is_preflight: bool
    warnings: List[str] = field(default_factory=list)

    def passed(self) -> bool:
        return len(self.warnings) == 0

    def display(self) -> str:
        lines = [
            f"CORS Request : {'yes' if self.is_cors_request else 'no'}",
            f"Preflight    : {'yes' if self.is_preflight else 'no'}",
            f"Origin       : {self.origin or '-'}",
            f"Allow-Origin : {self.allow_origin or '-'}",
            f"Allow-Methods: {self.allow_methods or '-'}",
            f"Credentials  : {'yes' if self.allow_credentials else 'no'}",
        ]
        if self.warnings:
            lines.append("Warnings:")
            for w in self.warnings:
                lines.append(f"  ! {w}")
        return "\n".join(lines)


def _header(headers: dict, key: str) -> Optional[str]:
    for k, v in headers.items():
        if k.lower() == key.lower():
            return v
    return None


def analyze_cors(req: CapturedRequest, resp: CapturedResponse) -> CORSInfo:
    origin = _header(req.headers, "origin")
    is_cors = origin is not None
    is_preflight = req.method.upper() == "OPTIONS" and is_cors

    allow_origin = _header(resp.headers, "access-control-allow-origin")
    allow_methods = _header(resp.headers, "access-control-allow-methods")
    allow_headers = _header(resp.headers, "access-control-allow-headers")
    allow_creds_raw = _header(resp.headers, "access-control-allow-credentials")
    allow_credentials = (allow_creds_raw or "").lower() == "true"

    warnings: List[str] = []
    if is_cors and not allow_origin:
        warnings.append("Missing Access-Control-Allow-Origin in response")
    if allow_origin == "*" and allow_credentials:
        warnings.append("Wildcard Allow-Origin with Allow-Credentials is invalid")
    if is_preflight and not allow_methods:
        warnings.append("Preflight response missing Access-Control-Allow-Methods")

    return CORSInfo(
        is_cors_request=is_cors,
        origin=origin,
        allow_origin=allow_origin,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
        allow_credentials=allow_credentials,
        is_preflight=is_preflight,
        warnings=warnings,
    )
