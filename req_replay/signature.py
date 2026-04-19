"""Request signature generation and verification."""
from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Optional

from req_replay.models import CapturedRequest


@dataclass
class SignatureResult:
    request_id: str
    algorithm: str
    signature: str
    verified: Optional[bool] = None

    def display(self) -> str:
        lines = [
            f"Request : {self.request_id}",
            f"Algorithm: {self.algorithm}",
            f"Signature: {self.signature}",
        ]
        if self.verified is not None:
            status = "✓ valid" if self.verified else "✗ invalid"
            lines.append(f"Status   : {status}")
        return "\n".join(lines)


def _canonical_string(req: CapturedRequest) -> str:
    """Build a stable canonical string from request fields."""
    headers_str = json.dumps(
        {k.lower(): v for k, v in sorted(req.headers.items())}, sort_keys=True
    )
    return "\n".join([
        req.method.upper(),
        req.url,
        headers_str,
        req.body or "",
    ])


def sign_request(
    req: CapturedRequest,
    secret: str,
    algorithm: str = "sha256",
) -> SignatureResult:
    """Generate an HMAC signature for a captured request."""
    if algorithm not in ("sha256", "sha512"):
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    canonical = _canonical_string(req)
    sig = hmac.new(
        secret.encode(), canonical.encode(), getattr(hashlib, algorithm)
    ).hexdigest()
    return SignatureResult(
        request_id=req.id,
        algorithm=algorithm,
        signature=sig,
    )


def verify_request(
    req: CapturedRequest,
    secret: str,
    expected_signature: str,
    algorithm: str = "sha256",
) -> SignatureResult:
    """Verify a request signature against an expected value."""
    result = sign_request(req, secret, algorithm)
    result.verified = hmac.compare_digest(result.signature, expected_signature)
    return result
