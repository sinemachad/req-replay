"""Compute and compare stable hashes of request headers."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Dict, List, Optional

from req_replay.models import CapturedRequest


@dataclass
class HeaderHashResult:
    request_id: str
    algorithm: str
    digest: str
    header_count: int

    def display(self) -> str:
        return (
            f"Request : {self.request_id}\n"
            f"Algorithm: {self.algorithm}\n"
            f"Headers  : {self.header_count}\n"
            f"Digest   : {self.digest}"
        )

    def to_dict(self) -> Dict:
        return {
            "request_id": self.request_id,
            "algorithm": self.algorithm,
            "digest": self.digest,
            "header_count": self.header_count,
        }


def _canonical_headers(headers: Dict[str, str]) -> str:
    """Return a stable, sorted, lowercased JSON representation of headers."""
    normalised = {k.lower().strip(): v.strip() for k, v in headers.items()}
    ordered = sorted(normalised.items())
    return json.dumps(ordered, separators=(",", ":"))


def hash_headers(
    request: CapturedRequest,
    algorithm: str = "sha256",
) -> HeaderHashResult:
    """Compute a hash of the request's headers."""
    supported = {"sha256", "sha1", "md5"}
    if algorithm not in supported:
        raise ValueError(f"Unsupported algorithm '{algorithm}'. Choose from {supported}.")

    canonical = _canonical_headers(request.headers)
    h = hashlib.new(algorithm, canonical.encode())
    return HeaderHashResult(
        request_id=request.id,
        algorithm=algorithm,
        digest=h.hexdigest(),
        header_count=len(request.headers),
    )


def compare_header_hashes(
    a: CapturedRequest,
    b: CapturedRequest,
    algorithm: str = "sha256",
) -> bool:
    """Return True if both requests have identical header digests."""
    return (
        hash_headers(a, algorithm).digest == hash_headers(b, algorithm).digest
    )


def batch_hash(
    requests: List[CapturedRequest],
    algorithm: str = "sha256",
) -> List[HeaderHashResult]:
    """Hash headers for a list of requests."""
    return [hash_headers(r, algorithm) for r in requests]
