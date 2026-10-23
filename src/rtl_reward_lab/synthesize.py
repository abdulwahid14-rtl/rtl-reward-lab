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

    The flow (`synth -top <module>; flatten; stat; ltp`) is intentionally
    fixed so that cell count and logic depth are comparable across
    candidates and the reference implementation.

    Two things make naive regex extraction wrong here, both handled below:

    1. `flatten` is required: without it, our own `stat` call reports
       per-module statistics, so a hierarchical design's top-level section
       only counts one "cell" per submodule instance (not that submodule's
       internal cells).
    2. `synth` itself prints its own internal, pre-flatten, per-module stat
       report as part of its normal flow, *before* our explicit `stat`
       command ever runs. That means stdout contains multiple "Number of
       cells:" lines, and the first one belongs to synth's own report, not
       ours. We take the *last* match of each metric so we read our final,
       post-flatten `stat`/`ltp` instead of synth's internal one.
    """

    script = f'read_verilog -sv "{source_path}"; synth -top {top_module}; flatten; stat; ltp'
    run_result = run(["yosys", "-p", script], cwd=cwd, limits=limits)

    if run_result.timed_out or run_result.returncode != 0:
        return SynthesizeResult(ok=False, metrics=None, run_result=run_result)

    cell_matches = _CELL_COUNT_RE.findall(run_result.stdout)
    depth_matches = _LONGEST_PATH_RE.findall(run_result.stdout)
    if not cell_matches or not depth_matches:
        return SynthesizeResult(ok=False, metrics=None, run_result=run_result)

    metrics = SynthesisMetrics(
        cell_count=int(cell_matches[-1]),
        logic_depth=int(depth_matches[-1]),
    )
    return SynthesizeResult(ok=True, metrics=metrics, run_result=run_result)
