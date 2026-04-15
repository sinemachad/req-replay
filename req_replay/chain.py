"""Request chaining: run a sequence of stored requests in order,
passing values extracted from each response into subsequent requests."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.replay import replay_request, ReplayResult
from req_replay.storage import RequestStore


@dataclass
class ChainStep:
    """One step in a request chain."""
    request_id: str
    # Extractions: {variable_name: json_path_or_header_name}
    # Prefix 'header:' to pull from response headers, else treated as JSON body key.
    extract: Dict[str, str] = field(default_factory=dict)
    # Header overrides applied before replay, supports {var} interpolation.
    header_overrides: Dict[str, str] = field(default_factory=dict)


@dataclass
class ChainResult:
    step_index: int
    request_id: str
    result: ReplayResult
    extracted: Dict[str, str] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.result.passed

    @property
    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] step {self.step_index + 1} ({self.request_id}): {self.result.summary}"


def _interpolate(value: str, variables: Dict[str, str]) -> str:
    """Replace {var_name} placeholders with values from variables dict."""
    def replacer(match: re.Match) -> str:
        key = match.group(1)
        return variables.get(key, match.group(0))
    return re.sub(r"\{(\w+)\}", replacer, value)


def _extract_variables(
    response: CapturedResponse,
    extract: Dict[str, str],
) -> Dict[str, str]:
    extracted: Dict[str, str] = {}
    body_json: Optional[Dict[str, Any]] = None
    if response.body:
        import json
        try:
            body_json = json.loads(response.body)
        except (ValueError, TypeError):
            body_json = None

    for var_name, selector in extract.items():
        if selector.startswith("header:"):
            header_key = selector[len("header:"):].lower()
            for k, v in response.headers.items():
                if k.lower() == header_key:
                    extracted[var_name] = v
                    break
        elif body_json is not None and selector in body_json:
            extracted[var_name] = str(body_json[selector])
    return extracted


def run_chain(
    steps: List[ChainStep],
    store: RequestStore,
) -> List[ChainResult]:
    """Execute a chain of requests sequentially.

    Returns a list of ChainResult, one per step.  Stops on first failure.
    """
    results: List[ChainResult] = []
    variables: Dict[str, str] = {}

    for idx, step in enumerate(steps):
        req: CapturedRequest = store.load(step.request_id)

        # Apply header overrides with variable interpolation
        if step.header_overrides:
            merged_headers = dict(req.headers)
            for k, v in step.header_overrides.items():
                merged_headers[k] = _interpolate(v, variables)
            req = CapturedRequest(
                id=req.id,
                method=req.method,
                url=req.url,
                headers=merged_headers,
                body=req.body,
                timestamp=req.timestamp,
                tags=req.tags,
            )

        replay_result = replay_request(req)
        extracted = _extract_variables(replay_result.actual, step.extract)
        variables.update(extracted)

        chain_result = ChainResult(
            step_index=idx,
            request_id=step.request_id,
            result=replay_result,
            extracted=extracted,
        )
        results.append(chain_result)

        if not chain_result.passed:
            break

    return results
