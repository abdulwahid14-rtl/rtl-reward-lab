"""Compile and run trusted simulations."""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

from rtl_reward_lab.runner import RunLimits, RunResult, run

_MISMATCH_RE = re.compile(r"Total mismatched samples is (\d+) out of (\d+) samples")


@dataclasses.dataclass(frozen=True)
class SimulateResult:
    """Outcome of compiling and running a candidate against the trusted testbench."""

    passed: bool
    stage: str  # "compile", "simulate", or "done"
    mismatches: int | None
    total_samples: int | None
    compile_result: RunResult
    simulate_result: RunResult | None


def simulate(
    candidate_path: str | Path,
    reference_path: str | Path,
    test_path: str | Path,
    *,
    cwd: str | Path,
    limits: RunLimits | None = None,
    extra_sources: tuple[str | Path, ...] = (),
) -> SimulateResult:
    """Compile candidate, reference, and the official test with Icarus Verilog,
    then run the simulation and decide pass/fail from the testbench's own
    mismatch count.

    The testbench (not this function) is the source of truth: it must finish
    and report "Total mismatched samples is 0 out of N samples" for the run
    to be considered passing.

    `extra_sources` are additional files compiled alongside the three main
    ones, unchanged otherwise. evaluator.py uses this to re-simulate a
    Yosys-written gate-level netlist (as `candidate_path`) together with
    Yosys's `simcells.v` behavioral models, so that the design actually
    synthesized is also the one functionally checked.
    """

    compiled_vvp = "simulation.vvp"
    compile_result = run(
        [
            "iverilog",
            "-g2012",
            "-s",
            "tb",
            "-o",
            compiled_vvp,
            str(candidate_path),
            str(reference_path),
            str(test_path),
            *(str(p) for p in extra_sources),
        ],
        cwd=cwd,
        limits=limits,
    )
    if compile_result.timed_out or compile_result.returncode != 0:
        return SimulateResult(
            passed=False,
            stage="compile",
            mismatches=None,
            total_samples=None,
            compile_result=compile_result,
            simulate_result=None,
        )

    simulate_result = run(["vvp", "-N", compiled_vvp], cwd=cwd, limits=limits)
    if simulate_result.timed_out or simulate_result.returncode != 0:
        return SimulateResult(
            passed=False,
            stage="simulate",
            mismatches=None,
            total_samples=None,
            compile_result=compile_result,
            simulate_result=simulate_result,
        )

    matches = _MISMATCH_RE.findall(simulate_result.stdout)
    if len(matches) != 1:
        # Zero matches means the testbench never reached its own report line
        # (e.g. it crashed or was starved of time). More than one match means
        # something other than the trusted testbench's own final report wrote
        # a line matching this pattern -- most plausibly a candidate trying to
        # forge a passing result via $display. Either way, don't trust it.
        return SimulateResult(
            passed=False,
            stage="simulate",
            mismatches=None,
            total_samples=None,
            compile_result=compile_result,
            simulate_result=simulate_result,
        )

    mismatches, total_samples = int(matches[0][0]), int(matches[0][1])
    return SimulateResult(
        passed=mismatches == 0,
        stage="done",
        mismatches=mismatches,
        total_samples=total_samples,
        compile_result=compile_result,
        simulate_result=simulate_result,
    )
