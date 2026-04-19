"""Pipeline: run a sequence of transforms and assertions against a stored request."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from req_replay.models import CapturedRequest, CapturedResponse
from req_replay.transform import TransformConfig, transform_request
from req_replay.assert_rules import AssertionRule, AssertionResult, evaluate
from req_replay.replay import replay_request
from req_replay.diff import DiffResult


@dataclass
class PipelineStep:
    name: str
    transform: Optional[TransformConfig] = None
    rules: List[AssertionRule] = field(default_factory=list)


@dataclass
class StepResult:
    step_name: str
    assertion_results: List[AssertionResult] = field(default_factory=list)
    diff: Optional[DiffResult] = None
    error: Optional[str] = None

    @property
    def passed(self) -> bool:
        if self.error:
            return False
        return all(r.passed for r in self.assertion_results)

    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        lines = [f"[{status}] {self.step_name}"]
        for r in self.assertion_results:
            mark = "✓" if r.passed else "✗"
            lines.append(f"  {mark} {r.rule}")
        if self.error:
            lines.append(f"  error: {self.error}")
        return "\n".join(lines)


@dataclass
class PipelineResult:
    step_results: List[StepResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(s.passed for s in self.step_results)

    def summary(self) -> str:
        lines = [s.summary() for s in self.step_results]
        overall = "PASS" if self.passed else "FAIL"
        lines.append(f"Pipeline: {overall} ({sum(s.passed for s in self.step_results)}/{len(self.step_results)} steps passed)")
        return "\n".join(lines)


def run_pipeline(
    request: CapturedRequest,
    steps: List[PipelineStep],
    baseline: Optional[CapturedResponse] = None,
) -> PipelineResult:
    results: List[StepResult] = []
    for step in steps:
        req = request
        if step.transform:
            req = transform_request(req, step.transform)
        try:
            replay_result = replay_request(req, baseline)
            response = replay_result.actual
            assertion_results = [evaluate(rule, response) for rule in step.rules]
            results.append(StepResult(
                step_name=step.name,
                assertion_results=assertion_results,
                diff=replay_result.diff,
            ))
        except Exception as exc:  # noqa: BLE001
            results.append(StepResult(step_name=step.name, error=str(exc)))
    return PipelineResult(step_results=results)
