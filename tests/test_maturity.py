"""Tests for req_replay.maturity."""
import pytest
from req_replay.models import CapturedRequest
from req_replay.maturity import score_request, MaturityResult


def _req(**kwargs) -> CapturedRequest:
    defaults = dict(
        id="test-id",
        method="GET",
        url="https://example.com/api",
        headers={"User-Agent": "test", "Content-Type": "application/json"},
        body=None,
        tags=["smoke"],
        metadata={"captured_at": "2024-01-01T00:00:00"},
    )
    defaults.update(kwargs)
    return CapturedRequest(**defaults)


def test_perfect_request_scores_100():
    result = score_request(_req())
    assert result.score == 100
    assert result.issues == []
    assert result.grade == "A"


def test_no_headers_deducts_20():
    result = score_request(_req(headers={}))
    assert result.score <= 80
    codes = [i.code for i in result.issues]
    assert "M001" in codes


def test_missing_content_type_with_body_deducts():
    result = score_request(_req(headers={"User-Agent": "x"}, body=b"{}", method="POST"))
    codes = [i.code for i in result.issues]
    assert "M002" in codes


def test_no_tags_deducts():
    result = score_request(_req(tags=[]))
    codes = [i.code for i in result.issues]
    assert "M003" in codes


def test_post_without_body_deducts():
    result = score_request(_req(method="POST", body=None))
    codes = [i.code for i in result.issues]
    assert "M004" in codes


def test_http_url_deducts():
    result = score_request(_req(url="http://example.com/api"))
    codes = [i.code for i in result.issues]
    assert "M006" in codes


def test_score_never_negative():
    result = score_request(_req(
        headers={}, tags=[], body=None, method="POST",
        url="http://example.com", metadata={},
    ))
    assert result.score >= 0


def test_grade_boundaries():
    def _r(score):
        r = MaturityResult(request_id="x", score=score)
        return r.grade
    assert _r(100) == "A"
    assert _r(90) == "A"
    assert _r(89) == "B"
    assert _r(75) == "B"
    assert _r(74) == "C"
    assert _r(60) == "C"
    assert _r(59) == "D"
    assert _r(40) == "D"
    assert _r(39) == "F"


def test_display_contains_grade():
    result = score_request(_req())
    text = result.display()
    assert "Grade" in text
    assert result.request_id in text
