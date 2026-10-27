"""Execute tools with isolation and limits."""

from __future__ import annotations

import dataclasses
import os
import resource
import selectors
import signal
import subprocess
import time
from pathlib import Path

_READ_CHUNK = 64 * 1024


@dataclasses.dataclass(frozen=True)
class RunLimits:
    """Resource limits applied to a subprocess."""

    timeout_seconds: float = 30.0
    cpu_seconds: int = 30
    memory_bytes: int = 512 * 1024 * 1024
    # Per-file size cap (RLIMIT_FSIZE) for files the child writes: VCD
    # traces, compiled .vvp images, synthesized netlists. A longer-running
    # trusted testbench (thousands of clock cycles) can legitimately dump a
    # multi-megabyte VCD trace via $dumpvars even for a correct candidate --
    # confirmed empirically (a correct BCD-counter candidate's VCD trace is
    # ~1.2 MB). A 1 MiB cap silently kills vvp mid-dump with SIGXFSZ, which
    # earlier surfaced as a false "simulate" failure indistinguishable from a
    # real functional mismatch. 16 MiB keeps a real bound (this is still a
    # hard cap, not unlimited) while covering every task in this project's
    # test suite and experiments.
    max_file_bytes: int = 16 * 1024 * 1024
    # Combined stdout + stderr cap, enforced by the parent while it reads the
    # pipes. RLIMIT_FSIZE does not apply to pipes, so without this a child
    # flooding warnings would grow the parent's memory without bound. Kept
    # separate from max_file_bytes so a large-but-legitimate VCD doesn't
    # force a large log allowance, or the reverse.
    max_log_bytes: int = 4 * 1024 * 1024


@dataclasses.dataclass(frozen=True)
class RunResult:
    """Outcome of executing a command."""

    command: list[str]
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool
    # True if the child was killed for exceeding limits.max_log_bytes;
    # stdout/stderr then hold only the bytes read before the cap.
    output_overflow: bool = False


def _preexec(limits: RunLimits):
    def _apply() -> None:
        os.setsid()
        resource.setrlimit(resource.RLIMIT_CPU, (limits.cpu_seconds, limits.cpu_seconds))
        resource.setrlimit(resource.RLIMIT_AS, (limits.memory_bytes, limits.memory_bytes))
        resource.setrlimit(resource.RLIMIT_FSIZE, (limits.max_file_bytes, limits.max_file_bytes))

    return _apply


def _kill_group(pid: int) -> None:
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def run(command: list[str], *, cwd: str | Path, limits: RunLimits | None = None) -> RunResult:
    """Run a trusted tool (e.g. iverilog, vvp, yosys) in an isolated subprocess.

    The child runs in its own process group, confined to ``cwd``, with
    CPU time, address space, and file size limits applied before exec.
    stdout and stderr are read incrementally against a single combined byte
    budget (``limits.max_log_bytes``); the entire process group is killed if
    that budget is exceeded or if it runs past ``limits.timeout_seconds``
    wall-clock time.
    """

    limits = limits or RunLimits()

    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=_preexec(limits),
    )

    stdout_fd, stderr_fd = process.stdout.fileno(), process.stderr.fileno()
    chunks: dict[int, list[bytes]] = {stdout_fd: [], stderr_fd: []}
    captured = 0
    timed_out = False
    output_overflow = False
    deadline = time.monotonic() + limits.timeout_seconds

    with selectors.DefaultSelector() as selector:
        selector.register(process.stdout, selectors.EVENT_READ)
        selector.register(process.stderr, selectors.EVENT_READ)
        while selector.get_map() and not output_overflow:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                break
            for key, _ in selector.select(remaining):
                data = os.read(key.fd, _READ_CHUNK)
                if not data:
                    selector.unregister(key.fileobj)
                    continue
                chunks[key.fd].append(data[: limits.max_log_bytes - captured])
                captured += len(data)
                if captured > limits.max_log_bytes:
                    output_overflow = True
                    break

    if timed_out or output_overflow:
        _kill_group(process.pid)
    process.stdout.close()
    process.stderr.close()

    # Both pipes can hit EOF while the child is still running (it closed or
    # redirected them), so the wait is bounded by the same deadline.
    try:
        process.wait(timeout=max(deadline - time.monotonic(), 0))
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_group(process.pid)
        process.wait()

    def _decode(fd: int) -> str:
        return b"".join(chunks[fd]).decode("utf-8", errors="replace")

    return RunResult(
        command=list(command),
        returncode=None if timed_out else process.returncode,
        stdout=_decode(stdout_fd),
        stderr=_decode(stderr_fd),
        timed_out=timed_out,
        output_overflow=output_overflow,
    )
