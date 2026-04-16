"""Pre/post replay hooks for running shell commands or Python callables."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from req_replay.models import CapturedRequest, CapturedResponse


@dataclass
class HookConfig:
    """Configuration for pre- and post-replay hooks."""
    pre_shell: List[str] = field(default_factory=list)
    post_shell: List[str] = field(default_factory=list)
    pre_callable: Optional[Callable[[CapturedRequest], CapturedRequest]] = None
    post_callable: Optional[Callable[[CapturedRequest, CapturedResponse], None]] = None
    timeout: int = 10


@dataclass
class HookResult:
    request: CapturedRequest
    response: CapturedResponse
    pre_outputs: List[str] = field(default_factory=list)
    post_outputs: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        status = "OK" if self.passed else "FAILED"
        lines = [f"Hook run [{status}]"]
        if self.pre_outputs:
            lines.append(f"  pre : {len(self.pre_outputs)} command(s) ran")
        if self.post_outputs:
            lines.append(f"  post: {len(self.post_outputs)} command(s) ran")
        if self.errors:
            for e in self.errors:
                lines.append(f"  error: {e}")
        return "\n".join(lines)


def _run_shell(cmd: str, timeout: int) -> tuple[str, Optional[str]]:
    """Run a shell command; return (stdout, error_message|None)."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            return result.stdout, f"Command exited {result.returncode}: {result.stderr.strip()}"
        return result.stdout, None
    except subprocess.TimeoutExpired:
        return "", f"Command timed out after {timeout}s: {cmd}"
    except Exception as exc:  # pragma: no cover
        return "", str(exc)


def run_hooks(
    request: CapturedRequest,
    response: CapturedResponse,
    config: HookConfig,
) -> HookResult:
    """Execute pre/post hooks around an already-completed replay result."""
    pre_outputs: List[str] = []
    post_outputs: List[str] = []
    errors: List[str] = []
    current_request = request

    # Pre callable
    if config.pre_callable is not None:
        try:
            current_request = config.pre_callable(current_request)
        except Exception as exc:
            errors.append(f"pre_callable raised: {exc}")

    # Pre shell commands
    for cmd in config.pre_shell:
        out, err = _run_shell(cmd, config.timeout)
        pre_outputs.append(out)
        if err:
            errors.append(err)

    # Post shell commands
    for cmd in config.post_shell:
        out, err = _run_shell(cmd, config.timeout)
        post_outputs.append(out)
        if err:
            errors.append(err)

    # Post callable
    if config.post_callable is not None:
        try:
            config.post_callable(current_request, response)
        except Exception as exc:
            errors.append(f"post_callable raised: {exc}")

    return HookResult(
        request=current_request,
        response=response,
        pre_outputs=pre_outputs,
        post_outputs=post_outputs,
        errors=errors,
    )
