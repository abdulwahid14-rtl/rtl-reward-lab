"""Compare candidate and reference behavior."""

from __future__ import annotations

import dataclasses
from pathlib import Path

from rtl_reward_lab.runner import RunLimits, RunResult, run

_GOLD_MODULE = "TopModule"
_GATE_MODULE = "RefModule"


@dataclasses.dataclass(frozen=True)
class FormalResult:
    """Outcome of a SAT-based equivalence check between candidate and reference."""

    equivalent: bool
    run_result: RunResult


def check_equivalence(
    candidate_path: str | Path,
    reference_path: str | Path,
    *,
    cwd: str | Path,
    limits: RunLimits | None = None,
) -> FormalResult:
    """Prove, via a SAT-based miter, that the candidate's `TopModule` is
    functionally equivalent to the reference's `RefModule` for every
    input, not just the vectors exercised by the testbench.

    This is a combinational equivalence check: any internal state
    (registers) is treated as free, so it is exact for purely
    combinational designs and only approximate for sequential ones. It
    complements, not replaces, simulate.py's vector-based pass/fail.
    """

    script = (
        f'read_verilog -sv "{candidate_path}" "{reference_path}"; '
        "hierarchy -check; "
        f"miter -equiv -make_assert {_GOLD_MODULE} {_GATE_MODULE} miter; "
        "flatten miter; "
        "sat -prove-asserts -verify miter"
    )
    run_result = run(["yosys", "-p", script], cwd=cwd, limits=limits)

    equivalent = (
        not run_result.timed_out
        and not run_result.output_overflow
        and run_result.returncode == 0
        and "SUCCESS" in run_result.stdout
    )
    return FormalResult(equivalent=equivalent, run_result=run_result)
