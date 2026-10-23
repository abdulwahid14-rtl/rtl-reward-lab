"""Execute tools with isolation and limits."""

from __future__ import annotations

import dataclasses
import os
import resource
import signal
import subprocess
from pathlib import Path


@dataclasses.dataclass(frozen=True)
class RunLimits:
    """Resource limits applied to a subprocess."""

    timeout_seconds: float = 30.0
    cpu_seconds: int = 30
    memory_bytes: int = 512 * 1024 * 1024
    # A longer-running trusted testbench (thousands of clock cycles) can
    # legitimately dump a multi-megabyte VCD trace via $dumpvars even for a
    # correct candidate -- confirmed empirically (a correct BCD-counter
    # candidate's VCD trace is ~1.2 MB). A 1 MiB cap silently kills vvp
    # mid-dump with SIGXFSZ, which earlier surfaced as a false "simulate"
    # failure indistinguishable from a real functional mismatch. 16 MiB
    # keeps a real bound (this is still a hard cap, not unlimited) while
    # covering every task in this project's test suite and experiments.
    max_output_bytes: int = 16 * 1024 * 1024


@dataclasses.dataclass(frozen=True)
class RunResult:
    """Outcome of executing a command."""

    command: list[str]
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool


def _preexec(limits: RunLimits):
    def _apply() -> None:
        os.setsid()
        resource.setrlimit(resource.RLIMIT_CPU, (limits.cpu_seconds, limits.cpu_seconds))
        resource.setrlimit(resource.RLIMIT_AS, (limits.memory_bytes, limits.memory_bytes))
        resource.setrlimit(resource.RLIMIT_FSIZE, (limits.max_output_bytes, limits.max_output_bytes))

    return _apply


def run(command: list[str], *, cwd: str | Path, limits: RunLimits | None = None) -> RunResult:
    """Run a trusted tool (e.g. iverilog, vvp, yosys) in an isolated subprocess.

    The child runs in its own process group, confined to ``cwd``, with
    CPU time, address space, and output file size limits applied before
    exec. If it exceeds ``limits.timeout_seconds`` wall-clock time, the
    entire process group is killed.
    """

    limits = limits or RunLimits()

    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=_preexec(limits),
    )

    try:
        stdout, stderr = process.communicate(timeout=limits.timeout_seconds)
        return RunResult(
            command=list(command),
            returncode=process.returncode,
            stdout=stdout,
            stderr=stderr,
            timed_out=False,
        )
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
        return RunResult(
            command=list(command),
            returncode=None,
            stdout=stdout,
            stderr=stderr,
            timed_out=True,
        )
