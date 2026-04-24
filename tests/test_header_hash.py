"""Tests for req_replay.header_hash."""
from __future__ import annotations

import pytest

from req_replay.header_hash import (
    HeaderHashResult,
    _canonical_headers,
    batch_hash,
    compare_header_hashes,
    hash_headers,
)
from req_replay.models import CapturedRequest


def _req(headers: dict | None = None, rid: str = "r1") -> CapturedRequest:
    return CapturedRequest(
        id=rid,
        method="GET",
        url="https://example.com/api",
        headers=headers or {"Content-Type": "application/json", "Authorization": "Bearer tok"},
        body=None,
        timestamp="2024-01-01T00:00:00Z",
        tags=[],
        metadata={},
    )


def test_canonical_headers_sorted():
    h = {"Z-Header": "z", "A-Header": "a"}
    canon = _canonical_headers(h)
    assert canon.index("a-header") < canon.index("z-header")


def test_canonical_headers_lowercased():
    h = {"Content-Type": "application/json"}
    canon = _canonical_headers(h)
    assert "content-type" in canon
    assert "Content-Type" not in canon


def test_canonical_headers_strips_whitespace():
    h = {"  X-Key  ": "  value  "}
    canon = _canonical_headers(h)
    assert "x-key" in canon
    assert "value" in canon
    assert "  " not in canon


def test_hash_headers_returns_result():
    req = _req()
    result = hash_headers(req)
    assert isinstance(result, HeaderHashResult)
    assert result.request_id == "r1"
    assert result.algorithm == "sha256"
    assert len(result.digest) == 64
    assert result.header_count == 2


def test_hash_headers_sha1():
    req = _req()
    result = hash_headers(req, algorithm="sha1")
    assert result.algorithm == "sha1"
    assert len(result.digest) == 40


def test_hash_headers_md5():
    req = _req()
    result = hash_headers(req, algorithm="md5")
    assert result.algorithm == "md5"
    assert len(result.digest) == 32


def test_hash_headers_unsupported_algorithm_raises():
    req = _req()
    with pytest.raises(ValueError, match="Unsupported algorithm"):
        hash_headers(req, algorithm="blake2b")


def test_hash_is_stable():
    req = _req()
    assert hash_headers(req).digest == hash_headers(req).digest


def test_different_headers_produce_different_hashes():
    r1 = _req({"X-A": "1"}, rid="r1")
    r2 = _req({"X-A": "2"}, rid="r2")
    assert hash_headers(r1).digest != hash_headers(r2).digest


def test_compare_identical_headers_returns_true():
    r1 = _req({"X-A": "v"}, rid="r1")
    r2 = _req({"X-A": "v"}, rid="r2")
    assert compare_header_hashes(r1, r2) is True


def test_compare_different_headers_returns_false():
    r1 = _req({"X-A": "v1"}, rid="r1")
    r2 = _req({"X-A": "v2"}, rid="r2")
    assert compare_header_hashes(r1, r2) is False


def test_batch_hash_returns_one_per_request():
    reqs = [_req({"X-N": str(i)}, rid=f"r{i}") for i in range(4)]
    results = batch_hash(reqs)
    assert len(results) == 4
    digests = [r.digest for r in results]
    assert len(set(digests)) == 4


def test_display_contains_digest():
    req = _req()
    result = hash_headers(req)
    display = result.display()
    assert result.digest in display
    assert result.algorithm in display


def test_to_dict_keys():
    req = _req()
    result = hash_headers(req)
    d = result.to_dict()
    assert set(d.keys()) == {"request_id", "algorithm", "digest", "header_count"}
