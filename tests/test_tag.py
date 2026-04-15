"""Tests for req_replay.tag."""
from __future__ import annotations

import pytest

from req_replay.models import CapturedRequest
from req_replay.tag import TagSummary, add_tags, remove_tags, summarize_tags


def _req(id: str = "abc", tags: list[str] | None = None) -> CapturedRequest:
    return CapturedRequest(
        id=id,
        timestamp="2024-01-01T00:00:00",
        method="GET",
        url="https://example.com/api",
        headers={},
        body=None,
        tags=tags or [],
    )


def test_add_tags_merges_new_tags() -> None:
    req = _req(tags=["smoke"])
    updated = add_tags(req, ["regression", "ci"])
    assert set(updated.tags) == {"smoke", "regression", "ci"}


def test_add_tags_deduplicates() -> None:
    req = _req(tags=["smoke"])
    updated = add_tags(req, ["smoke", "smoke"])
    assert updated.tags.count("smoke") == 1


def test_add_tags_returns_sorted() -> None:
    req = _req(tags=[])
    updated = add_tags(req, ["z-tag", "a-tag"])
    assert updated.tags == ["a-tag", "z-tag"]


def test_add_tags_does_not_mutate_original() -> None:
    req = _req(tags=["smoke"])
    add_tags(req, ["new"])
    assert req.tags == ["smoke"]


def test_remove_tags_removes_specified() -> None:
    req = _req(tags=["smoke", "regression", "ci"])
    updated = remove_tags(req, ["regression"])
    assert "regression" not in updated.tags
    assert "smoke" in updated.tags
    assert "ci" in updated.tags


def test_remove_tags_ignores_absent_tags() -> None:
    req = _req(tags=["smoke"])
    updated = remove_tags(req, ["nonexistent"])
    assert updated.tags == ["smoke"]


def test_remove_tags_does_not_mutate_original() -> None:
    req = _req(tags=["smoke", "ci"])
    remove_tags(req, ["smoke"])
    assert req.tags == ["smoke", "ci"]


def test_summarize_tags_counts_correctly() -> None:
    requests = [
        _req(id="1", tags=["smoke", "ci"]),
        _req(id="2", tags=["smoke"]),
        _req(id="3", tags=["regression"]),
    ]
    summaries = summarize_tags(requests)
    by_tag = {s.tag: s for s in summaries}
    assert by_tag["smoke"].count == 2
    assert by_tag["ci"].count == 1
    assert by_tag["regression"].count == 1


def test_summarize_tags_empty_returns_empty() -> None:
    assert summarize_tags([]) == []


def test_summarize_tags_no_tags_returns_empty() -> None:
    requests = [_req(id="1", tags=[]), _req(id="2", tags=[])]
    assert summarize_tags(requests) == []


def test_tag_summary_display() -> None:
    s = TagSummary(tag="smoke", count=3, request_ids=["a", "b", "c"])
    assert "smoke" in s.display()
    assert "3" in s.display()
