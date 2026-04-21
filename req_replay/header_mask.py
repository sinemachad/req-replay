"""Header masking — selectively redact or truncate header values before display or storage."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from req_replay.models import CapturedRequest

# Headers that are considered sensitive by default and should be masked.
_DEFAULT_SENSITIVE: Set[str] = {
    "authorization",
    "proxy-authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-auth-token",
    "x-secret",
    "x-access-token",
    "x-csrf-token",
}

_MASK_PLACEHOLDER = "***"


@dataclass
class MaskResult:
    """Outcome of masking a single request's headers."""

    original_headers: Dict[str, str]
    masked_headers: Dict[str, str]
    masked_keys: List[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        """Return True if at least one header value was masked."""
        return len(self.masked_keys) > 0

    def display(self) -> str:
        """Human-readable summary of what was masked."""
        if not self.changed:
            return "No headers masked."
        lines = ["Masked headers:"]
        for key in sorted(self.masked_keys):
            lines.append(f"  {key}: {self.masked_headers[key]}")
        return "\n".join(lines)


def _mask_value(value: str, visible_chars: int = 4) -> str:
    """Return a masked version of *value*, preserving the last *visible_chars* characters.

    If the value is shorter than or equal to *visible_chars*, the entire value
    is replaced with the placeholder.
    """
    if len(value) <= visible_chars:
        return _MASK_PLACEHOLDER
    return _MASK_PLACEHOLDER + value[-visible_chars:]


def mask_headers(
    headers: Dict[str, str],
    sensitive: Optional[Set[str]] = None,
    extra_pattern: Optional[str] = None,
    visible_chars: int = 4,
) -> MaskResult:
    """Mask sensitive header values in *headers*.

    Args:
        headers: Mapping of header name to value (case-insensitive matching).
        sensitive: Set of lowercase header names to treat as sensitive.  When
            ``None`` the built-in :data:`_DEFAULT_SENSITIVE` set is used.
        extra_pattern: Optional regex pattern; any header whose name matches
            this pattern (case-insensitive) will also be masked.
        visible_chars: How many trailing characters to leave visible after the
            mask placeholder.

    Returns:
        A :class:`MaskResult` containing the original headers, the masked
        copy, and the list of keys that were masked.
    """
    if sensitive is None:
        sensitive = _DEFAULT_SENSITIVE

    compiled: Optional[re.Pattern[str]] = None
    if extra_pattern:
        compiled = re.compile(extra_pattern, re.IGNORECASE)

    masked: Dict[str, str] = {}
    masked_keys: List[str] = []

    for key, value in headers.items():
        normalised = key.lower()
        should_mask = normalised in sensitive or (
            compiled is not None and compiled.search(key) is not None
        )
        if should_mask:
            masked[key] = _mask_value(value, visible_chars=visible_chars)
            masked_keys.append(key)
        else:
            masked[key] = value

    return MaskResult(
        original_headers=dict(headers),
        masked_headers=masked,
        masked_keys=masked_keys,
    )


def mask_request_headers(
    request: CapturedRequest,
    sensitive: Optional[Set[str]] = None,
    extra_pattern: Optional[str] = None,
    visible_chars: int = 4,
) -> MaskResult:
    """Convenience wrapper that applies :func:`mask_headers` to a captured request.

    The *request* object is **not** mutated; the masked headers are available
    via the returned :class:`MaskResult`.
    """
    return mask_headers(
        headers=request.headers,
        sensitive=sensitive,
        extra_pattern=extra_pattern,
        visible_chars=visible_chars,
    )
