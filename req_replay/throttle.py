"""Throttle replay: rate-limit replays with configurable delay and burst control."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Iterator, List, Optional

from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.replay import ReplayResult, replay_request
from req_replay.storage import RequestStore


@dataclass
class ThrottleConfig:
    """Configuration for throttled replay."""
    delay_seconds: float = 1.0          # pause between each request
    burst: int = 1                       # how many requests to fire before pausing
    max_requests: Optional[int] = None   # cap total replays (None = all)


@dataclass
class ThrottleEvent:
    iteration: int
    request_id: str
    result: ReplayResult
    elapsed: float  # seconds taken for this single replay

    @property
    def passed(self) -> bool:
        return self.result.passed

    @property
    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return (
            f"[{status}] iteration={self.iteration} id={self.request_id} "
            f"elapsed={self.elapsed:.3f}s"
        )


@dataclass
class ThrottleResult:
    events: List[ThrottleEvent] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(e.passed for e in self.events)

    @property
    def summary(self) -> str:
        total = len(self.events)
        failures = sum(1 for e in self.events if not e.passed)
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {total} replayed, {failures} failed"


def throttle_replay(
    request_ids: List[str],
    store: RequestStore,
    config: Optional[ThrottleConfig] = None,
    *,
    _replay_fn: Callable[[CapturedRequest, Optional[CapturedResponse]], ReplayResult] = replay_request,
    _sleep_fn: Callable[[float], None] = time.sleep,
) -> ThrottleResult:
    """Replay *request_ids* honouring burst and delay settings."""
    cfg = config or ThrottleConfig()
    result = ThrottleResult()
    ids = request_ids[: cfg.max_requests] if cfg.max_requests is not None else request_ids

    for idx, req_id in enumerate(ids, start=1):
        captured = store.load(req_id)
        baseline: Optional[CapturedResponse] = getattr(captured, "response", None)

        t0 = time.monotonic()
        replay_result = _replay_fn(captured, baseline)
        elapsed = time.monotonic() - t0

        result.events.append(
            ThrottleEvent(
                iteration=idx,
                request_id=req_id,
                result=replay_result,
                elapsed=elapsed,
            )
        )

        # pause after every *burst* requests, except after the last one
        if idx % cfg.burst == 0 and idx < len(ids):
            _sleep_fn(cfg.delay_seconds)

    return result
