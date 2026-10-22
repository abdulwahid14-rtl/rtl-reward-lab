"""Run a fixed Yosys flow and extract metrics."""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

from rtl_reward_lab.reward import SynthesisMetrics
from rtl_reward_lab.runner import RunLimits, RunResult, run

_CELL_COUNT_RE = re.compile(r"Number of cells:\s+(\d+)")
_LONGEST_PATH_RE = re.compile(r"Longest topological path in \S+ \(length=(\d+)\)")


@dataclasses.dataclass(frozen=True)
class SynthesizeResult:
    """Outcome of running the fixed Yosys flow on a single RTL source."""

    ok: bool
    metrics: SynthesisMetrics | None
    run_result: RunResult


def synthesize(
    source_path: str | Path,
    *,
    top_module: str,
    cwd: str | Path,
    limits: RunLimits | None = None,
) -> SynthesizeResult:
    """Run a fixed synth + stat + ltp flow over a single source file and
    extract its cell count and logic depth.

    The flow (`synth -top <module>; stat; ltp`) is intentionally fixed so
    that cell count and logic depth are comparable across candidates and
    the reference implementation.
    """

    script = f'read_verilog -sv "{source_path}"; synth -top {top_module}; stat; ltp'
    run_result = run(["yosys", "-p", script], cwd=cwd, limits=limits)

    if run_result.timed_out or run_result.returncode != 0:
        return SynthesizeResult(ok=False, metrics=None, run_result=run_result)

    cell_match = _CELL_COUNT_RE.search(run_result.stdout)
    depth_match = _LONGEST_PATH_RE.search(run_result.stdout)
    if cell_match is None or depth_match is None:
        return SynthesizeResult(ok=False, metrics=None, run_result=run_result)

    metrics = SynthesisMetrics(
        cell_count=int(cell_match.group(1)),
        logic_depth=int(depth_match.group(1)),
    )
    return SynthesizeResult(ok=True, metrics=metrics, run_result=run_result)
