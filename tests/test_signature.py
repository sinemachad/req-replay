"""Tests for req_replay.signature."""
import hashlib
import hmac
import json

import pytest

from req_replay.models import CapturedRequest
from req_replay.signature import (
    SignatureResult,
    _canonical_string,
    sign_request,
    verify_request,
)


def _req(**kwargs) -> CapturedRequest:
    defaults = dict(
        id="r1",
        method="POST",
        url="https://example.com/api",
        headers={"Content-Type": "application/json"},
        body='{"key": "value"}',
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )
    defaults.update(kwargs)
    return CapturedRequest(**defaults)


def test_canonical_string_is_stable():
    req = _req()
    c1 = _canonical_string(req)
    c2 = _canonical_string(req)
    assert c1 == c2


def test_canonical_string_includes_method_and_url():
    req = _req(method="GET", url="https://example.com/")
    c = _canonical_string(req)
    assert "GET" in c
    assert "https://example.com/" in c


def test_canonical_string_normalises_header_case():
    req_lower = _req(headers={"content-type": "application/json"})
    req_upper = _req(headers={"Content-Type": "application/json"})
    assert _canonical_string(req_lower) == _canonical_string(req_upper)


def test_sign_returns_signature_result():
    req = _req()
    result = sign_request(req, "mysecret")
    assert isinstance(result, SignatureResult)
    assert result.request_id == "r1"
    assert result.algorithm == "sha256"
    assert len(result.signature) == 64  # sha256 hex


def test_sign_sha512_produces_128_char_hex():
    req = _req()
    result = sign_request(req, "mysecret", algorithm="sha512")
    assert len(result.signature) == 128


def test_sign_unsupported_algorithm_raises():
    with pytest.raises(ValueError, match="Unsupported"):
        sign_request(_req(), "s", algorithm="md5")


def test_sign_matches_manual_hmac():
    req = _req()
    canonical = _canonical_string(req)
    expected = hmac.new(b"mysecret", canonical.encode(), hashlib.sha256).hexdigest()
    result = sign_request(req, "mysecret")
    assert result.signature == expected


def test_verify_correct_signature_passes():
    req = _req()
    signed = sign_request(req, "s3cr3t")
    result = verify_request(req, "s3cr3t", signed.signature)
    assert result.verified is True


def test_verify_wrong_signature_fails():
    req = _req()
    result = verify_request(req, "s3cr3t", "deadbeef" * 8)
    assert result.verified is False


def test_display_contains_signature():
    req = _req()
    result = sign_request(req, "k")
    display = result.display()
    assert result.signature in display
    assert "sha256" in display


def test_display_with_verified_shows_status():
    req = _req()
    signed = sign_request(req, "k")
    verified = verify_request(req, "k", signed.signature)
    assert "valid" in verified.display()
