"""Generate HTML or JSON summary reports from replay/diff results."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from req_replay.diff import DiffResult


@dataclass
class ReportEntry:
    request_id: str
    url: str
    method: str
    passed: bool
    status_match: bool
    body_match: bool
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "url": self.url,
            "method": self.method,
            "passed": self.passed,
            "status_match": self.status_match,
            "body_match": self.body_match,
            "notes": self.notes,
        }


@dataclass
class Report:
    entries: List[ReportEntry] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.entries)

    @property
    def passed(self) -> int:
        return sum(1 for e in self.entries if e.passed)

    @property
    def failed(self) -> int:
        return self.total - self.passed

    def summary(self) -> str:
        return f"Report: {self.passed}/{self.total} passed, {self.failed} failed"

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "entries": [e.to_dict() for e in self.entries],
        }


def build_report(pairs: list[tuple[str, str, str, DiffResult]]) -> Report:
    """Build a Report from (request_id, method, url, DiffResult) tuples."""
    entries = []
    for request_id, method, url, diff in pairs:
        entries.append(ReportEntry(
            request_id=request_id,
            url=url,
            method=method,
            passed=diff.is_identical,
            status_match=diff.status_match,
            body_match=diff.body_match,
        ))
    return Report(entries=entries)


def save_report_json(report: Report, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2))


def save_report_html(report: Report, path: Path) -> None:
    rows = ""
    for e in report.entries:
        status = "✅" if e.passed else "❌"
        rows += (
            f"<tr><td>{status}</td><td>{e.request_id}</td>"
            f"<td>{e.method}</td><td>{e.url}</td>"
            f"<td>{'✅' if e.status_match else '❌'}</td>"
            f"<td>{'✅' if e.body_match else '❌'}</td></tr>\n"
        )
    html = (
        "<html><body>"
        f"<h1>req-replay Report</h1><p>{report.summary()}</p>"
        "<table border='1'><tr><th>Pass</th><th>ID</th><th>Method</th>"
        "<th>URL</th><th>Status</th><th>Body</th></tr>"
        f"{rows}</table></body></html>"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html)
