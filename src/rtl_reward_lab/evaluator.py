"""Orchestrate all stages."""

from __future__ import annotations

import dataclasses
from pathlib import Path

from rtl_reward_lab.runner import RunLimits
from rtl_reward_lab.simulate import SimulateResult, simulate


@dataclasses.dataclass(frozen=True)
class EvaluationResult:
    """Combined outcome of all evaluation stages run so far."""

    passed: bool
    stage: str  # "simulate", "formal", "synthesize", or "done"
    simulate_result: SimulateResult


def evaluate(
    candidate_path: str | Path,
    reference_path: str | Path,
    test_path: str | Path,
    *,
    cwd: str | Path,
    limits: RunLimits | None = None,
) -> EvaluationResult:
    """Run each evaluation stage in order, stopping at the first failure.

    Only compilation and simulation (via simulate.py) are implemented so
    far. Formal equivalence checking (formal.py) and synthesis metric
    extraction (synthesize.py) are later stages: once implemented, they
    must run only after simulation passes, short-circuiting on failure the
    same way this function already does.
    """

    sim_result = simulate(candidate_path, reference_path, test_path, cwd=cwd, limits=limits)
    if not sim_result.passed:
        return EvaluationResult(passed=False, stage="simulate", simulate_result=sim_result)

    return EvaluationResult(passed=True, stage="done", simulate_result=sim_result)
