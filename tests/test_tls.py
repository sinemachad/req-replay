"""Tests for req_replay.tls."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from req_replay.tls import TLSInfo, _parse_rdn, inspect_tls


def _make_info(expires: datetime | None = None, san=None) -> TLSInfo:
    return TLSInfo(
        host="example.com",
        port=443,
        subject={"commonName": "example.com"},
        issuer={"organizationName": "Test CA"},
        version="3",
        expires=expires,
        san=san or ["example.com", "www.example.com"],
    )


def test_not_expired_future():
    info = _make_info(expires=datetime.utcnow() + timedelta(days=60))
    assert not info.expired()


def test_expired_past():
    info = _make_info(expires=datetime.utcnow() - timedelta(days=1))
    assert info.expired()


def test_days_until_expiry_positive():
    info = _make_info(expires=datetime.utcnow() + timedelta(days=45))
    days = info.days_until_expiry()
    assert days is not None
    assert 44 <= days <= 45


def test_days_until_expiry_none_when_no_expires():
    info = _make_info(expires=None)
    assert info.days_until_expiry() is None


def test_expired_returns_false_when_no_expires():
    info = _make_info(expires=None)
    assert not info.expired()


def test_display_contains_host():
    info = _make_info(expires=datetime.utcnow() + timedelta(days=10))
    assert "example.com" in info.display()


def test_display_contains_issuer():
    info = _make_info()
    assert "Test CA" in info.display()


def test_parse_rdn_extracts_values():
    rdn_seq = [[("commonName", "example.com")], [("organizationName", "Acme")]]
    result = _parse_rdn(rdn_seq)
    assert result["commonName"] == "example.com"
    assert result["organizationName"] == "Acme"


def test_parse_rdn_empty():
    assert _parse_rdn([]) == {}


def _fake_cert():
    return {
        "subject": [[("commonName", "example.com")]],
        "issuer": [[("organizationName", "Test CA")]],
        "version": 3,
        "notAfter": "Dec 31 23:59:59 2099 GMT",
        "subjectAltName": [("DNS", "example.com"), ("DNS", "www.example.com")],
    }


def test_inspect_tls_returns_tls_info():
    mock_ssock = MagicMock()
    mock_ssock.getpeercert.return_value = _fake_cert()
    mock_ssock.__enter__ = lambda s: s
    mock_ssock.__exit__ = MagicMock(return_value=False)

    mock_sock = MagicMock()
    mock_sock.__enter__ = lambda s: s
    mock_sock.__exit__ = MagicMock(return_value=False)

    with patch("req_replay.tls.socket.create_connection", return_value=mock_sock), \
         patch("req_replay.tls.ssl.create_default_context") as mock_ctx:
        ctx_inst = MagicMock()
        ctx_inst.wrap_socket.return_value = mock_ssock
        mock_ctx.return_value = ctx_inst

        info = inspect_tls("https://example.com")

    assert info.host == "example.com"
    assert info.port == 443
    assert "example.com" in info.san
    assert info.expires is not None
    assert not info.expired()
