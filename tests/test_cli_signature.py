"""Tests for req_replay.cli_signature."""
import pytest
from click.testing import CliRunner

from req_replay.cli_signature import signature_group
from req_replay.models import CapturedRequest
from req_replay.signature import sign_request
from req_replay.storage import RequestStore


def _make_request(rid: str = "req-1") -> CapturedRequest:
    return CapturedRequest(
        id=rid,
        method="GET",
        url="https://example.com/",
        headers={},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
        metadata={},
    )


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def store_path(tmp_path):
    return str(tmp_path / "store")


def _populate(store_path: str, req: CapturedRequest) -> None:
    store = RequestStore(store_path)
    store.save(req)


def test_sign_missing_request_shows_error(runner, store_path):
    result = runner.invoke(
        signature_group, ["sign", "missing-id", "--secret", "s", "--store", store_path]
    )
    assert result.exit_code != 0
    assert "not found" in result.output


def test_sign_outputs_signature(runner, store_path):
    req = _make_request()
    _populate(store_path, req)
    result = runner.invoke(
        signature_group, ["sign", req.id, "--secret", "mysecret", "--store", store_path]
    )
    assert result.exit_code == 0
    assert "sha256" in result.output
    assert "Signature" in result.output


def test_sign_unsupported_algorithm_exits(runner, store_path):
    req = _make_request()
    _populate(store_path, req)
    result = runner.invoke(
        signature_group,
        ["sign", req.id, "--secret", "s", "--algorithm", "md5", "--store", store_path],
    )
    assert result.exit_code != 0


def test_verify_correct_signature_exits_zero(runner, store_path):
    req = _make_request()
    _populate(store_path, req)
    sig = sign_request(req, "mysecret").signature
    result = runner.invoke(
        signature_group,
        ["verify", req.id, "--secret", "mysecret", "--signature", sig, "--store", store_path],
    )
    assert result.exit_code == 0
    assert "valid" in result.output


def test_verify_wrong_signature_exits_nonzero(runner, store_path):
    req = _make_request()
    _populate(store_path, req)
    result = runner.invoke(
        signature_group,
        ["verify", req.id, "--secret", "mysecret", "--signature", "bad" * 20, "--store", store_path],
    )
    assert result.exit_code != 0
    assert "invalid" in result.output


def test_verify_missing_request_shows_error(runner, store_path):
    result = runner.invoke(
        signature_group,
        ["verify", "ghost", "--secret", "s", "--signature", "abc", "--store", store_path],
    )
    assert result.exit_code != 0
    assert "not found" in result.output
