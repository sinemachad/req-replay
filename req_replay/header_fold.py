"""Header folding: detect and unfold multi-line header values (obs-fold)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from req_replay.models import CapturedRequest

# RFC 7230 §3.2.6 – obs-fold is a SP or HTAB after a CRLF inside a header value.
_OBS_FOLD_CHARS = (" ", "\t")


@dataclass
class FoldWarning:
    header: str
    original_value: str
    code: str = "HF001"

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "header": self.header,
            "original_value": self.original_value,
        }


@dataclass
class FoldResult:
    warnings: List[FoldWarning] = field(default_factory=list)
    unfolded: Dict[str, str] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return len(self.warnings) == 0

    def summary(self) -> str:
        if self.passed:
            return "OK – no obs-fold header values detected"
        codes = ", ".join(w.code for w in self.warnings)
        return f"WARN – {len(self.warnings)} folded header(s) detected [{codes}]"


def _is_folded(value: str) -> bool:
    """Return True if *value* contains an obs-fold sequence."""
    return "\n" in value or "\r" in value


def _unfold(value: str) -> str:
    """Replace obs-fold whitespace sequences with a single space."""
    import re
    return re.sub(r"\r?\n[ \t]+", " ", value).strip()


def analyze_header_fold(request: CapturedRequest) -> FoldResult:
    """Detect obs-fold values in *request* headers and return an unfolded copy."""
    warnings: List[FoldWarning] = []
    unfolded: Dict[str, str] = {}

    for key, value in (request.headers or {}).items():
        if _is_folded(value):
            warnings.append(FoldWarning(header=key.lower(), original_value=value))
            unfolded[key] = _unfold(value)
        else:
            unfolded[key] = value

    return FoldResult(warnings=warnings, unfolded=unfolded)
