"""Payload analysis: detect encoding, type, and size of request/response bodies."""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Optional

from req_replay.models import CapturedRequest, CapturedResponse


@dataclass
class PayloadInfo:
    encoding: str          # 'json', 'form', 'base64', 'text', 'empty', 'unknown'
    size_bytes: int
    is_binary: bool
    preview: str           # first 120 chars of decoded content

    def display(self) -> str:
        lines = [
            f"  Encoding : {self.encoding}",
            f"  Size     : {self.size_bytes} bytes",
            f"  Binary   : {self.is_binary}",
            f"  Preview  : {self.preview}",
        ]
        return "\n".join(lines)


def _content_type(headers: dict[str, str]) -> str:
    for k, v in headers.items():
        if k.lower() == "content-type":
            return v.lower()
    return ""


def _is_base64(value: str) -> bool:
    try:
        base64.b64decode(value, validate=True)
        return True
    except Exception:
        return False


def analyze_payload(body: Optional[str], headers: dict[str, str]) -> PayloadInfo:
    if not body:
        return PayloadInfo(encoding="empty", size_bytes=0, is_binary=False, preview="")

    ct = _content_type(headers)
    size = len(body.encode("utf-8", errors="replace"))

    if "application/json" in ct:
        try:
            json.loads(body)
            encoding = "json"
        except ValueError:
            encoding = "unknown"
        return PayloadInfo(encoding=encoding, size_bytes=size, is_binary=False, preview=body[:120])

    if "application/x-www-form-urlencoded" in ct:
        return PayloadInfo(encoding="form", size_bytes=size, is_binary=False, preview=body[:120])

    if _is_base64(body):
        return PayloadInfo(encoding="base64", size_bytes=size, is_binary=True, preview=body[:120])

    if "text/" in ct:
        return PayloadInfo(encoding="text", size_bytes=size, is_binary=False, preview=body[:120])

    return PayloadInfo(encoding="unknown", size_bytes=size, is_binary=False, preview=body[:120])


def analyze_request_payload(req: CapturedRequest) -> PayloadInfo:
    return analyze_payload(req.body, req.headers)


def analyze_response_payload(resp: CapturedResponse) -> PayloadInfo:
    return analyze_payload(resp.body, resp.headers)
