"""Tests for req_replay.cli_maturity."""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from req_replay.cli_maturity import maturity_group
from req_replay.maturity import MaturityResult
from req_replay.models import CapturedRequest


def _make_request(rid="abc-123") -> CapturedRequest:
    return CapturedRequest(
        id=rid,
        method="GET",
        url="https://example.com",
        headers={"User-Agent": "test"},
        body=None,
        tags=["ci"],
        metadata={},
    )


@pytest.fixture()
def runner():
    return CliRunner()


def test_score_missing_request_shows_error(runner, tmp_path):
    result = runner.invoke(maturity_group, ["score", "no-such-id", "--store", str(tmp_path)])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_score_displays_result(runner, tmp_path):
    req = _make_request()
    with patch("req_replay.cli_maturity.RequestStore") as MockStore:
        inst = MockStore.return_value
        inst.load.return_value = req
        res = runner.invoke(maturity_group, ["score", req.id, "--store", str(tmp_path)])
    assert res.exit_code == 0
    assert "Score" in res.output


def test_report_no_requests(runner, tmp_path):
    with patch("req_replay.cli_maturity.RequestStore") as MockStore:
        inst = MockStore.return_value
        inst.list.return_value = []
        res = runner.invoke(maturity_group, ["report", "--store", str(tmp_path)])
    assert "No requests" in res.output


def test_report_shows_table(runner, tmp_path):
    reqs = [_make_request(f"id-{i}") for i in range(3)]
    with patch("req_replay.cli_maturity.RequestStore") as MockStore:
        inst = MockStore.return_value
        inst.list.return_value = reqs
        res = runner.invoke(maturity_group, ["report", "--store", str(tmp_path)])
    assert res.exit_code == 0
    assert "Grade" in res.output


def test_report_min_score_filters(runner, tmp_path):
    req = _make_request()
    with patch("req_replay.cli_maturity.RequestStore") as MockStore:
        inst = MockStore.return_value
        inst.list.return_value = [req]
        res = runner.invoke(maturity_group, ["report", "--store", str(tmp_path), "--min-score", "200"])
    # All requests score < 200 so table should appear
    assert res.exit_code == 0
