"""Replay stored HTTP requests and compare responses."""

from dataclasses import dataclass, field
from typing import Optional

from req_replay.capture import _send_request, _build_captured_response
from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.storage import RequestStore


@dataclass
class ReplayResult:
    request_id: str
    original_response: CapturedResponse
    replayed_response: CapturedResponse
    status_match: bool = field(init=False)
    body_match: bool = field(init=False)

    def __post_init__(self):
        self.status_match = (
            self.original_response.status_code == self.replayed_response.status_code
        )
        self.body_match = self.original_response.body == self.replayed_response.body

    @property
    def passed(self) -> bool:
        return self.status_match and self.body_match

    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return (
            f"[{status}] Request {self.request_id} | "
            f"Status: {'✓' if self.status_match else '✗'} | "
            f"Body: {'✓' if self.body_match else '✗'}"
        )


def replay_request(
    request_id: str,
    store: RequestStore,
    override_url: Optional[str] = None,
) -> ReplayResult:
    """Replay a stored request and return a comparison result."""
    captured_req, original_resp = store.load(request_id)

    if override_url:
        captured_req = CapturedRequest(
            id=captured_req.id,
            method=captured_req.method,
            url=override_url,
            headers=captured_req.headers,
            body=captured_req.body,
            timestamp=captured_req.timestamp,
            tags=captured_req.tags,
        )

    response = _send_request(captured_req)
    replayed_resp = _build_captured_response(response)

    return ReplayResult(
        request_id=request_id,
        original_response=original_resp,
        replayed_response=replayed_resp,
    )
