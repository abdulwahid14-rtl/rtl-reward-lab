"""Orchestrate all stages."""

from __future__ import annotations

import dataclasses
from pathlib import Path

from rtl_reward_lab.formal import FormalResult, check_equivalence
from rtl_reward_lab.policy import PolicyResult, check_policy
from rtl_reward_lab.runner import RunLimits
from rtl_reward_lab.simulate import SimulateResult, simulate


@dataclasses.dataclass(frozen=True)
class EvaluationResult:
    """Combined outcome of all evaluation stages run so far."""

    passed: bool
    stage: str  # "policy", "simulate", or "done"
    policy_result: PolicyResult | None
    simulate_result: SimulateResult | None
    formal_result: FormalResult | None


def evaluate(
    candidate_path: str | Path,
    reference_path: str | Path,
    test_path: str | Path,
    *,
    cwd: str | Path,
    limits: RunLimits | None = None,
) -> EvaluationResult:
    """Run each evaluation stage in order, stopping at the first hard failure.

    1. policy.py: reject candidates that use disallowed constructs (file I/O,
       `$system`, simulation output, etc.) before any tool ever runs on them.
       This is a hard gate -- a rejection here is final.
    2. simulate.py: compile and run the candidate against the trusted
       testbench. This is the authoritative pass/fail signal and is also a
       hard gate.
    3. formal.py: once simulation passes, additionally attempt a SAT-based
       combinational equivalence check between candidate and reference as a
       diagnostic. This is NOT a gate: it is exact only for purely
       combinational designs. For sequential designs it treats each design's
       internal register state as independent/free, which produces false
       "not equivalent" results even for behaviorally-correct candidates
       (confirmed empirically on the pulse_shaping_fir task, which passes
       10000-cycle simulation with zero mismatches but fails this check).
       Its result is still recorded in the returned EvaluationResult for
       visibility, but a passing episode never depends on it. Making this
       check sound for sequential designs (e.g. via yosys's equiv_induct /
       temporal induction) is tracked as future work.

    synthesize.py (cell count / logic depth extraction) is not part of this
    function; it runs separately once a candidate passes, since its output
    feeds reward.py rather than a pass/fail decision.
    """

    candidate_source = (Path(cwd) / candidate_path).read_text()
    policy_result = check_policy(candidate_source)
    if not policy_result.allowed:
        return EvaluationResult(
            passed=False,
            stage="policy",
            policy_result=policy_result,
            simulate_result=None,
            formal_result=None,
        )

    sim_result = simulate(candidate_path, reference_path, test_path, cwd=cwd, limits=limits)
    if not sim_result.passed:
        return EvaluationResult(
            passed=False,
            stage="simulate",
            policy_result=policy_result,
            simulate_result=sim_result,
            formal_result=None,
        )

    formal_result = check_equivalence(candidate_path, reference_path, cwd=cwd, limits=limits)

    return EvaluationResult(
        passed=True,
        stage="done",
        policy_result=policy_result,
        simulate_result=sim_result,
        formal_result=formal_result,
    )
