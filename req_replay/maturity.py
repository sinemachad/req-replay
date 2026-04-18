"""Request maturity scoring — rates how 'complete' a captured request is."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from req_replay.models import CapturedRequest


@dataclass
class MaturityIssue:
    code: str
    message: str

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message}


@dataclass
class MaturityResult:
    request_id: str
    score: int  # 0-100
    issues: List[MaturityIssue] = field(default_factory=list)

    @property
    def grade(self) -> str:
        if self.score >= 90:
            return "A"
        if self.score >= 75:
            return "B"
        if self.score >= 60:
            return "C"
        if self.score >= 40:
            return "D"
        return "F"

    def display(self) -> str:
        lines = [f"Request : {self.request_id}",
                 f"Score   : {self.score}/100  (Grade {self.grade})"]
        if self.issues:
            lines.append("Issues:")
            for iss in self.issues:
                lines.append(f"  [{iss.code}] {iss.message}")
        else:
            lines.append("No issues found.")
        return "\n".join(lines)


_DEDUCTIONS = [
    ("M001", 20, lambda r: not r.headers, "No headers present"),
    ("M002", 10, lambda r: "content-type" not in {k.lower() for k in r.headers}
                           and r.body is not None, "Missing Content-Type with body"),
    ("M003", 10, lambda r: not r.tags, "No tags assigned"),
    ("M004", 15, lambda r: not r.body and r.method.upper() in ("POST", "PUT", "PATCH"),
     "No body for mutating request"),
    ("M005", 10, lambda r: "user-agent" not in {k.lower() for k in r.headers},
     "Missing User-Agent header"),
    ("M006", 10, lambda r: not r.url.startswith("https"), "URL uses plain HTTP"),
    ("M007", 5, lambda r: not getattr(r, 'metadata', None), "No metadata recorded"),
]


def score_request(req: CapturedRequest) -> MaturityResult:
    issues: List[MaturityIssue] = []
    deduction = 0
    for code, points, check, msg in _DEDUCTIONS:
        try:
            if check(req):
                issues.append(MaturityIssue(code=code, message=msg))
                deduction += points
        except Exception:
            pass
    score = max(0, 100 - deduction)
    return MaturityResult(request_id=req.id, score=score, issues=issues)
