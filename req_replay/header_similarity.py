"""Header similarity analysis between captured requests.

Computes pairwise Jaccard similarity of header key sets and identifies
requests that share a high proportion of headers — useful for spotting
duplication, misconfiguration, or templated clients.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from req_replay.models import CapturedRequest


@dataclass
class SimilarityPair:
    """Similarity score between two requests."""

    id_a: str
    id_b: str
    score: float  # Jaccard index in [0.0, 1.0]
    shared_headers: List[str] = field(default_factory=list)
    only_in_a: List[str] = field(default_factory=list)
    only_in_b: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id_a": self.id_a,
            "id_b": self.id_b,
            "score": round(self.score, 4),
            "shared_headers": self.shared_headers,
            "only_in_a": self.only_in_a,
            "only_in_b": self.only_in_b,
        }


@dataclass
class SimilarityReport:
    """Aggregated similarity report for a collection of requests."""

    pairs: List[SimilarityPair] = field(default_factory=list)
    threshold: float = 0.8

    @property
    def high_similarity_pairs(self) -> List[SimilarityPair]:
        """Return pairs whose score meets or exceeds the threshold."""
        return [p for p in self.pairs if p.score >= self.threshold]

    def display(self) -> str:  # pragma: no cover
        lines: List[str] = [
            f"Header Similarity Report (threshold={self.threshold:.0%})",
            f"  Total pairs analysed : {len(self.pairs)}",
            f"  High-similarity pairs: {len(self.high_similarity_pairs)}",
        ]
        for pair in self.high_similarity_pairs:
            lines.append(
                f"  {pair.id_a[:8]}…  <->  {pair.id_b[:8]}…  "
                f"score={pair.score:.2%}  shared={len(pair.shared_headers)}"
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------


def _header_keys(request: CapturedRequest) -> frozenset:
    """Return a normalised (lowercase) frozenset of header key names."""
    return frozenset(k.lower() for k in (request.headers or {}))


def _jaccard(a: frozenset, b: frozenset) -> float:
    """Compute the Jaccard index of two sets."""
    union = a | b
    if not union:
        return 1.0  # both empty → identical
    return len(a & b) / len(union)


def _compare_pair(
    req_a: CapturedRequest, req_b: CapturedRequest
) -> SimilarityPair:
    """Build a SimilarityPair for two requests."""
    keys_a = _header_keys(req_a)
    keys_b = _header_keys(req_b)
    score = _jaccard(keys_a, keys_b)
    return SimilarityPair(
        id_a=req_a.id,
        id_b=req_b.id,
        score=score,
        shared_headers=sorted(keys_a & keys_b),
        only_in_a=sorted(keys_a - keys_b),
        only_in_b=sorted(keys_b - keys_a),
    )


def analyze_similarity(
    requests: Sequence[CapturedRequest],
    threshold: float = 0.8,
    top_n: Optional[int] = None,
) -> SimilarityReport:
    """Compute pairwise header similarity for *requests*.

    Args:
        requests:  Sequence of captured requests to compare.
        threshold: Jaccard score at or above which a pair is considered
                   highly similar (default 0.8).
        top_n:     If given, only keep the *top_n* highest-scoring pairs
                   in the report (all pairs are still computed).

    Returns:
        A :class:`SimilarityReport` containing all pairwise scores.
    """
    reqs = list(requests)
    pairs: List[SimilarityPair] = []

    for i in range(len(reqs)):
        for j in range(i + 1, len(reqs)):
            pairs.append(_compare_pair(reqs[i], reqs[j]))

    # Sort descending by score for easier inspection
    pairs.sort(key=lambda p: p.score, reverse=True)

    if top_n is not None:
        pairs = pairs[:top_n]

    return SimilarityReport(pairs=pairs, threshold=threshold)
