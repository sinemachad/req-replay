"""Header templating: apply variable substitution to request headers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from req_replay.models import CapturedRequest


@dataclass
class TemplateResult:
    original: Dict[str, str]
    rendered: Dict[str, str]
    substitutions: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return self.original != self.rendered

    def display(self) -> str:
        lines = []
        if not self.changed:
            lines.append("No substitutions made.")
        else:
            for key in self.substitutions:
                orig = self.original.get(key, "")
                new = self.rendered.get(key, "")
                lines.append(f"  {key}: {orig!r} -> {new!r}")
        return "\n".join(lines)


def render_headers(
    headers: Dict[str, str],
    variables: Dict[str, str],
) -> TemplateResult:
    """Replace {{variable}} placeholders in header values."""
    original = dict(headers)
    rendered: Dict[str, str] = {}
    substitutions: List[str] = []

    for key, value in headers.items():
        new_value = value
        for var_name, var_value in variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            if placeholder in new_value:
                new_value = new_value.replace(placeholder, var_value)
        rendered[key] = new_value
        if new_value != value:
            substitutions.append(key)

    return TemplateResult(
        original=original,
        rendered=rendered,
        substitutions=substitutions,
    )


def render_request_headers(
    request: CapturedRequest,
    variables: Dict[str, str],
) -> CapturedRequest:
    """Return a new CapturedRequest with templated headers applied."""
    result = render_headers(request.headers, variables)
    return CapturedRequest(
        id=request.id,
        method=request.method,
        url=request.url,
        headers=result.rendered,
        body=request.body,
        timestamp=request.timestamp,
        tags=list(request.tags),
        metadata=dict(request.metadata),
    )
