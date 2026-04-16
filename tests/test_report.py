"""Tests for req_replay.report."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from req_replay.diff import DiffResult
from req_replay.report import Report, ReportEntry, build_report, save_report_json, save_report_html


def _diff(identical: bool, status_match: bool = True, body_match: bool = True) -> DiffResult:
    return DiffResult(
        is_identical=identical,
        status_match=status_match,
        body_match=body_match,
        header_diffs={},
    )


def test_report_counts():
    entries = [
        ReportEntry("a", "http://x.com", "GET", True, True, True),
        ReportEntry("b", "http://x.com", "POST", False, False, True),
    ]
    r = Report(entries=entries)
    assert r.total == 2
    assert r.passed == 1
    assert r.failed == 1


def test_report_summary_string():
    r = Report(entries=[
        ReportEntry("a", "http://x.com", "GET", True, True, True),
    ])
    assert "1/1" in r.summary()


def test_build_report_from_pairs():
    pairs = [
        ("id1", "GET", "http://example.com", _diff(True)),
        ("id2", "POST", "http://example.com/post", _diff(False, status_match=False, body_match=False)),
    ]
    report = build_report(pairs)
    assert report.total == 2
    assert report.passed == 1
    assert report.entries[1].status_match is False


def test_to_dict_structure():
    pairs = [("id1", "GET", "http://example.com", _diff(True))]
    d = build_report(pairs).to_dict()
    assert "entries" in d
    assert d["total"] == 1
    assert d["passed"] == 1


def test_save_report_json(tmp_path: Path):
    report = build_report([("id1", "GET", "http://x.com", _diff(True))])
    out = tmp_path / "report.json"
    save_report_json(report, out)
    data = json.loads(out.read_text())
    assert data["total"] == 1


def test_save_report_html(tmp_path: Path):
    report = build_report([("id1", "GET", "http://x.com", _diff(False, status_match=False, body_match=True))])
    out = tmp_path / "report.html"
    save_report_html(report, out)
    content = out.read_text()
    assert "<html>" in content
    assert "id1" in content


def test_save_report_creates_parent_dirs(tmp_path: Path):
    report = build_report([])
    out = tmp_path / "sub" / "dir" / "report.json"
    save_report_json(report, out)
    assert out.exists()
