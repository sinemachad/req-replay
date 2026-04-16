"""Tests for req_replay.hook."""
from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

from req_replay.hook import HookConfig, HookResult, run_hooks
from req_replay.models import CapturedRequest, CapturedResponse


def _req() -> CapturedRequest:
    return CapturedRequest(
        id="r1",
        method="GET",
        url="https://example.com/api",
        headers={},
        body=None,
        timestamp="2024-01-01T00:00:00",
        tags=[],
    )


def _resp() -> CapturedResponse:
    return CapturedResponse(
        status_code=200,
        headers={"content-type": "application/json"},
        body='{"ok": true}',
        elapsed_ms=42.0,
    )


def test_no_hooks_passes():
    result = run_hooks(_req(), _resp(), HookConfig())
    assert result.passed
    assert result.errors == []
    assert result.pre_outputs == []
    assert result.post_outputs == []


def test_pre_shell_success():
    cmd = f"{sys.executable} -c \"print('pre')\""
    config = HookConfig(pre_shell=[cmd])
    result = run_hooks(_req(), _resp(), config)
    assert result.passed
    assert len(result.pre_outputs) == 1
    assert "pre" in result.pre_outputs[0]


def test_post_shell_success():
    cmd = f"{sys.executable} -c \"print('post')\""
    config = HookConfig(post_shell=[cmd])
    result = run_hooks(_req(), _resp(), config)
    assert result.passed
    assert len(result.post_outputs) == 1


def test_shell_nonzero_exit_records_error():
    cmd = f"{sys.executable} -c \"raise SystemExit(1)\""
    config = HookConfig(pre_shell=[cmd])
    result = run_hooks(_req(), _resp(), config)
    assert not result.passed
    assert any("exited 1" in e for e in result.errors)


def test_shell_timeout_records_error():
    cmd = f"{sys.executable} -c \"import time; time.sleep(10)\""
    config = HookConfig(pre_shell=[cmd], timeout=1)
    result = run_hooks(_req(), _resp(), config)
    assert not result.passed
    assert any("timed out" in e for e in result.errors)


def test_pre_callable_transforms_request():
    def mutate(req: CapturedRequest) -> CapturedRequest:
        return CapturedRequest(
            id=req.id,
            method="POST",
            url=req.url,
            headers=req.headers,
            body=req.body,
            timestamp=req.timestamp,
            tags=req.tags,
        )

    config = HookConfig(pre_callable=mutate)
    result = run_hooks(_req(), _resp(), config)
    assert result.passed
    assert result.request.method == "POST"


def test_post_callable_is_called():
    called_with = []

    def after(req, resp):
        called_with.append((req, resp))

    config = HookConfig(post_callable=after)
    run_hooks(_req(), _resp(), config)
    assert len(called_with) == 1


def test_callable_exception_records_error():
    def bad_pre(req):
        raise ValueError("boom")

    config = HookConfig(pre_callable=bad_pre)
    result = run_hooks(_req(), _resp(), config)
    assert not result.passed
    assert any("boom" in e for e in result.errors)


def test_summary_ok():
    result = run_hooks(_req(), _resp(), HookConfig())
    assert "OK" in result.summary()


def test_summary_failed():
    cmd = f"{sys.executable} -c \"raise SystemExit(1)\""
    config = HookConfig(pre_shell=[cmd])
    result = run_hooks(_req(), _resp(), config)
    assert "FAILED" in result.summary()
    assert "error" in result.summary()
