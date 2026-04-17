"""Parameter extraction and analysis for captured requests."""
from __future__ import annotations
from dataclasses import dataclass, field
from urllib.parse import urlparse, parse_qs
from typing import Dict, List, Optional
import json

from req_replay.models import CapturedRequest


@dataclass
class ParamSummary:
    request_id: str
    url: str
    query_params: Dict[str, List[str]] = field(default_factory=dict)
    body_params: Dict[str, object] = field(default_factory=dict)
    path_params: Dict[str, str] = field(default_factory=dict)

    def display(self) -> str:
        lines = [f"Request : {self.request_id}", f"URL     : {self.url}"]
        if self.query_params:
            lines.append("Query Params:")
            for k, v in self.query_params.items():
                lines.append(f"  {k} = {', '.join(v)}")
        if self.body_params:
            lines.append("Body Params:")
            for k, v in self.body_params.items():
                lines.append(f"  {k} = {v}")
        if not self.query_params and not self.body_params:
            lines.append("  (no parameters found)")
        return "\n".join(lines)


def extract_query_params(url: str) -> Dict[str, List[str]]:
    parsed = urlparse(url)
    return parse_qs(parsed.query, keep_blank_values=True)


def extract_body_params(request: CapturedRequest) -> Dict[str, object]:
    content_type = ""
    for k, v in request.headers.items():
        if k.lower() == "content-type":
            content_type = v.lower()
            break

    body = request.body
    if not body:
        return {}

    if "application/json" in content_type:
        try:
            parsed = json.loads(body)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass

    if "application/x-www-form-urlencoded" in content_type:
        try:
            pairs = parse_qs(body if isinstance(body, str) else body.decode())
            return {k: v[0] if len(v) == 1 else v for k, v in pairs.items()}
        except Exception:
            pass

    return {}


def analyze_params(request: CapturedRequest) -> ParamSummary:
    return ParamSummary(
        request_id=request.id,
        url=request.url,
        query_params=extract_query_params(request.url),
        body_params=extract_body_params(request),
    )
