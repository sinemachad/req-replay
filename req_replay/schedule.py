"""Scheduled replay: run a stored request on a fixed interval."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Iterator, Optional

from req_replay.models import CapturedRequest
from req_replay.replay import ReplayResult, replay_request


@dataclass
class ScheduleConfig:
    """Configuration for a scheduled replay run."""

    interval_seconds: float = 60.0
    max_iterations: Optional[int] = None  # None => run forever
    stop_on_failure: bool = False
    tags: list[str] = field(default_factory=list)


@dataclass
class ScheduleEvent:
    iteration: int
    timestamp: datetime
    result: ReplayResult

    @property
    def passed(self) -> bool:
        return self.result.passed

    @property
    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        ts = self.timestamp.strftime("%Y-%m-%dT%H:%M:%S")
        return (
            f"[{ts}] iteration={self.iteration} {status} "
            f"| {self.result.diff.summary}"
        )


def schedule_replay(
    request: CapturedRequest,
    config: ScheduleConfig,
    *,
    on_event: Optional[Callable[[ScheduleEvent], None]] = None,
    _sleep: Callable[[float], None] = time.sleep,
) -> Iterator[ScheduleEvent]:
    """Replay *request* repeatedly according to *config*.

    Yields a :class:`ScheduleEvent` after each attempt.  Callers can
    also pass *on_event* to receive events via callback (useful for
    CLI integration).
    """
    iteration = 0
    while True:
        iteration += 1
        result = replay_request(request)
        event = ScheduleEvent(
            iteration=iteration,
            timestamp=datetime.utcnow(),
            result=result,
        )
        if on_event is not None:
            on_event(event)
        yield event

        if config.stop_on_failure and not event.passed:
            break
        if config.max_iterations is not None and iteration >= config.max_iterations:
            break
        _sleep(config.interval_seconds)
