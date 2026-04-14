"""HTTP request capture utilities using a proxy or direct interception."""

import time
import uuid
from typing import Optional, Dict

import requests
from requests import Response

from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.storage import RequestStore


def capture_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    body: Optional[str] = None,
    store: Optional[RequestStore] = None,
    tags: Optional[list] = None,
) -> tuple[CapturedRequest, CapturedResponse]:
    """Send an HTTP request, capture both request and response, and optionally store them."""
    headers = headers or {}
    tags = tags or []

    captured_req = CapturedRequest(
        id=str(uuid.uuid4()),
        method=method.upper(),
        url=url,
        headers=headers,
        body=body,
        timestamp=time.time(),
        tags=tags,
    )

    response = _send_request(captured_req)
    captured_resp = _build_captured_response(response)

    if store is not None:
        store.save(captured_req, captured_resp)

    return captured_req, captured_resp


def _send_request(req: CapturedRequest) -> Response:
    """Execute the HTTP request using the requests library."""
    return requests.request(
        method=req.method,
        url=req.url,
        headers=req.headers,
        data=req.body,
        timeout=30,
    )


def _build_captured_response(response: Response) -> CapturedResponse:
    """Build a CapturedResponse from a requests.Response object."""
    return CapturedResponse(
        status_code=response.status_code,
        headers=dict(response.headers),
        body=response.text,
        elapsed_ms=response.elapsed.total_seconds() * 1000,
    )
