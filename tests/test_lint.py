"""Tests for req_replay.lint."""
from __future__ import annotations

import pytest

from req_replay.models import CapturedRequest
from req_replay.lint import LintResult, LintWarning, lint_request


def _req(**kwargs) -> CapturedRequest:
    defaults = dict(
        id="abc123",
        method="GET",
        url="https://example.com/api",
        headers={},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
    )
    defaults.update(kwargs)
    return CapturedRequest(**defaults)


def test_clean_request_has_no_warnings():
    req = _req(tags=["smoke"])
    result = lint_request(req)
    assert result.warnings == []
    assert result.passed is True


def test_clean_request_summary_ok():
    req = _req(tags=["smoke"])
    result = lint_request(req)
    assert "OK" in result.summary


def test_l001_missing_content_type_on_post():
    req = _req(method="POST", tags=["t"])
    result = lint_request(req)
    codes = [w.code for w in result.warnings]
    assert "L001" in codes


def test_l001_not_raised_when_content_type_present():
    req = _req(method="POST", headers={"Content-Type": "application/json"}, tags=["t"])
    result = lint_request(req)
    codes = [w.code for w in result.warnings]
    assert "L001" not in codes


def test_l001_not_raised_for_get():
    req = _req(method="GET", tags=["t"])
    result = lint_request(req)
    codes = [w.code for w in result.warnings]
    assert "L001" not in codes


def test_l002_bare_auth_token():
    req = _req(headers={"Authorization": "mysecrettoken"}, tags=["t"])
    result = lint_request(req)
    codes = [w.code for w in result.warnings]
    assert "L002" in codes


def test_l002_not_raised_for_bearer_scheme():
    req = _req(headers={"Authorization": "Bearer abc.def.ghi"}, tags=["t"])
    result = lint_request(req)
    codes = [w.code for w in result.warnings]
    assert "L002" not in codes


def test_l003_url_with_credentials_is_error():
    req = _req(url="https://user:pass@example.com/api", tags=["t"])
    result = lint_request(req)
    codes = [w.code for w in result.warnings]
    assert "L003" in codes
    error_warnings = [w for w in result.warnings if w.code == "L003"]
    assert error_warnings[0].severity == "error"
    assert result.passed is False


def test_l004_plain_http():
    req = _req(url="http://example.com/api", tags=["t"])
    result = lint_request(req)
    codes = [w.code for w in result.warnings]
    assert "L004" in codes


def test_l005_no_tags():
    req = _req(tags=[])
    result = lint_request(req)
    codes = [w.code for w in result.warnings]
    assert "L005" in codes


def test_summary_lists_all_issues():
    req = _req(method="POST", url="http://example.com", tags=[])
    result = lint_request(req)
    summary = result.summary
    assert "L001" in summary
    assert "L004" in summary
    assert "L005" in summary


def test_lint_warning_to_dict():
    w = LintWarning(code="L001", message="test msg", severity="warning")
    d = w.to_dict()
    assert d == {"code": "L001", "message": "test msg", "severity": "warning"}
