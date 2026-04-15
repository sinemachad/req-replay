"""Tests for req_replay.annotate."""

from __future__ import annotations

import pytest

from req_replay.annotate import (
    Annotation,
    add_annotation,
    clear_annotations,
    get_annotations,
)
from req_replay.models import CapturedRequest


def _req(**kwargs) -> CapturedRequest:
    defaults = dict(
        id="req-1",
        method="GET",
        url="https://example.com/api",
        headers={},
        body=None,
        timestamp="2024-01-01T00:00:00+00:00",
        tags=[],
        metadata={},
    )
    defaults.update(kwargs)
    return CapturedRequest(**defaults)


def test_add_annotation_appends_note():
    req = _req()
    updated = add_annotation(req, note="first note")
    annotations = get_annotations(updated)
    assert len(annotations) == 1
    assert annotations[0].note == "first note"


def test_add_annotation_stores_author():
    req = _req()
    updated = add_annotation(req, note="check this", author="alice")
    annotations = get_annotations(updated)
    assert annotations[0].author == "alice"


def test_add_multiple_annotations():
    req = _req()
    req = add_annotation(req, note="note one")
    req = add_annotation(req, note="note two")
    annotations = get_annotations(req)
    assert len(annotations) == 2
    assert annotations[1].note == "note two"


def test_add_annotation_does_not_mutate_original():
    req = _req()
    _ = add_annotation(req, note="side-effect?")
    assert get_annotations(req) == []


def test_get_annotations_empty_when_none():
    req = _req()
    assert get_annotations(req) == []


def test_clear_annotations_removes_all():
    req = _req()
    req = add_annotation(req, note="a")
    req = add_annotation(req, note="b")
    cleared = clear_annotations(req)
    assert get_annotations(cleared) == []


def test_clear_annotations_preserves_other_metadata():
    req = _req(metadata={"env": "staging"})
    req = add_annotation(req, note="x")
    cleared = clear_annotations(req)
    assert cleared.metadata.get("env") == "staging"
    assert "annotations" not in cleared.metadata


def test_annotation_roundtrip_via_dict():
    ann = Annotation(note="roundtrip", author="bob", created_at="2024-06-01T12:00:00+00:00")
    restored = Annotation.from_dict(ann.to_dict())
    assert restored.note == ann.note
    assert restored.author == ann.author
    assert restored.created_at == ann.created_at


def test_annotation_created_at_is_set_automatically():
    ann = Annotation(note="auto time")
    assert ann.created_at != ""
    assert "T" in ann.created_at  # ISO format
