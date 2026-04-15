"""Retry logic for replaying requests with configurable backoff."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from req_replay.models import CapturedRequest
from req_replay.replay import ReplayResult, replay_request


@dataclass
class RetryConfig:
    max_attempts: int = 3
    backoff_seconds: float = 1.0
    backoff_multiplier: float = 2.0
    retry_on_status: List[int] = field(default_factory=lambda: [500, 502, 503, 504])
    retry_on_diff: bool = True


@dataclass
class RetryResult:
    attempts: int
    final_result: ReplayResult
    all_results: List[ReplayResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.final_result.passed

    @property
    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return (
            f"[{status}] completed in {self.attempts} attempt(s) — "
            f"{self.final_result.summary}"
        )


def retry_replay(
    request: CapturedRequest,
    config: Optional[RetryConfig] = None,
    base_url: Optional[str] = None,
) -> RetryResult:
    """Replay a request with retry logic based on RetryConfig."""
    if config is None:
        config = RetryConfig()

    results: List[ReplayResult] = []
    delay = config.backoff_seconds

    for attempt in range(1, config.max_attempts + 1):
        result = replay_request(request, base_url=base_url)
        results.append(result)

        should_retry = False
        if config.retry_on_diff and not result.passed:
            should_retry = True
        if result.response and result.response.status_code in config.retry_on_status:
            should_retry = True

        if not should_retry or attempt == config.max_attempts:
            return RetryResult(
                attempts=attempt,
                final_result=result,
                all_results=results,
            )

        time.sleep(delay)
        delay *= config.backoff_multiplier

    return RetryResult(
        attempts=config.max_attempts,
        final_result=results[-1],
        all_results=results,
    )
