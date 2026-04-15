"""Watch a stored request and re-replay it on a configurable interval."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, List, Optional

from req_replay.models import CapturedRequest
from req_replay.replay import ReplayResult, replay_request


@dataclass
class WatchEvent:
    """Single observation produced by the watcher."""

    timestamp: datetime
    result: ReplayResult
    iteration: int

    @property
    def passed(self) -> bool:  # noqa: D401
        return self.result.passed

    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return (
            f"[{self.timestamp.isoformat(timespec='seconds')}] "
            f"#{self.iteration} {status} — {self.result.summary()}"
        )


@dataclass
class WatchConfig:
    """Configuration for a watch session."""

    interval_seconds: float = 5.0
    max_iterations: Optional[int] = None
    stop_on_failure: bool = False
    ignore_headers: List[str] = field(default_factory=list)


def watch_request(
    request: CapturedRequest,
    config: WatchConfig,
    on_event: Optional[Callable[[WatchEvent], None]] = None,
) -> List[WatchEvent]:
    """Replay *request* repeatedly according to *config*.

    Calls *on_event* after each iteration (if provided) and returns the full
    list of :class:`WatchEvent` objects when the session ends.
    """
    events: List[WatchEvent] = []
    iteration = 0

    while True:
        iteration += 1
        result = replay_request(request, ignore_headers=config.ignore_headers)
        event = WatchEvent(
            timestamp=datetime.utcnow(),
            result=result,
            iteration=iteration,
        )
        events.append(event)

        if on_event is not None:
            on_event(event)

        if config.stop_on_failure and not event.passed:
            break

        if config.max_iterations is not None and iteration >= config.max_iterations:
            break

        time.sleep(config.interval_seconds)

    return events
