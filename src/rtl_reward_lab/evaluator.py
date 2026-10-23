"""Orchestrate all stages."""

from __future__ import annotations

import dataclasses
from pathlib import Path

from rtl_reward_lab.formal import FormalResult, check_equivalence
from rtl_reward_lab.policy import ALLOWED_TOP_MODULE, PolicyResult, check_policy
from rtl_reward_lab.runner import RunLimits
from rtl_reward_lab.simulate import SimulateResult, simulate
from rtl_reward_lab.synthesize import SynthesizeResult, find_simcells_v, synthesize

_NETLIST_FILENAME = "_candidate_netlist.v"

# A gate-level netlist (one primitive cell per $_AND_/$_DFFE_PN0P_/etc, each
# needing its own behavioral model from simcells.v) compiles to a much
# larger iverilog .vvp bytecode file than the same design's RTL source --
# e.g. ~1.02 MB for a design whose RTL-level build is a few hundred KB.
# RunLimits' default max_output_bytes (1 MiB) is sized for RTL-level
# compiles and is too tight for this, so it's floored here regardless of
# what the caller passed in.
_MIN_NETLIST_SIMULATE_OUTPUT_BYTES = 16 * 1024 * 1024


def _with_netlist_output_floor(limits: RunLimits | None) -> RunLimits:
    base = limits or RunLimits()
    if base.max_output_bytes >= _MIN_NETLIST_SIMULATE_OUTPUT_BYTES:
        return base
    return dataclasses.replace(base, max_output_bytes=_MIN_NETLIST_SIMULATE_OUTPUT_BYTES)


@dataclasses.dataclass(frozen=True)
class EvaluationResult:
    """Combined outcome of all evaluation stages run so far."""

    passed: bool
    stage: str  # "policy", "simulate", "synthesize", "netlist_simulate", or "done"
    policy_result: PolicyResult | None
    simulate_result: SimulateResult | None
    candidate_synth_result: SynthesizeResult | None
    netlist_simulate_result: SimulateResult | None
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
       `$system`, simulation output, preprocessor conditionals, etc.) before
       any tool ever runs on them. This is a hard gate -- a rejection here
       is final.
    2. simulate.py: compile and run the candidate's *source* against the
       trusted testbench. A hard gate, and a cheap first filter before
       paying synthesis's cost.
    3. synthesize.py: synthesize the candidate, which also produces the
       cell count / logic depth that reward.py uses. A hard gate -- if
       synthesis itself fails, there's nothing to reward.
    4. simulate.py again, this time on the *synthesized netlist* written by
       step 3 (with Yosys's `simcells.v` behavioral models alongside it),
       against the same trusted testbench. Also a hard gate.

       Step 4 exists because steps 2 and 3 each run a different tool over
       the candidate's source, and nothing before this forced their two
       views of the design to agree. A candidate guarding behavior behind
       a `` `ifdef SYNTHESIS `` conditional -- which Yosys defines by
       default and Icarus Verilog does not -- could pass step 2 with
       correct behavior while step 3 synthesizes a trivially small,
       functionally wrong design from the other branch, collecting a
       reward for a design that was never actually verified (confirmed
       empirically: an `ifdef`-guarded always-zero popcount3 candidate
       scored a full 2.0 before this gate existed). Re-simulating the
       actual netlist closes this: whatever synthesis produced is what
       gets checked.
    5. formal.py: once both simulations pass, additionally attempt a
       SAT-based combinational equivalence check between candidate and
       reference as a diagnostic. This is NOT a gate: it is exact only for
       purely combinational designs. For sequential designs it treats each
       design's internal register state as independent/free, which
       produces false "not equivalent" results even for behaviorally-correct
       candidates (confirmed empirically on the pulse_shaping_fir task,
       which passes 10000-cycle simulation with zero mismatches but fails
       this check). Its result is still recorded in the returned
       EvaluationResult for visibility, but a passing episode never depends
       on it. Making this check sound for sequential designs (e.g. via
       yosys's equiv_induct / temporal induction) is tracked as future work.
    """

    candidate_source = (Path(cwd) / candidate_path).read_text()
    policy_result = check_policy(candidate_source)
    if not policy_result.allowed:
        return EvaluationResult(
            passed=False,
            stage="policy",
            policy_result=policy_result,
            simulate_result=None,
            candidate_synth_result=None,
            netlist_simulate_result=None,
            formal_result=None,
        )

    sim_result = simulate(candidate_path, reference_path, test_path, cwd=cwd, limits=limits)
    if not sim_result.passed:
        return EvaluationResult(
            passed=False,
            stage="simulate",
            policy_result=policy_result,
            simulate_result=sim_result,
            candidate_synth_result=None,
            netlist_simulate_result=None,
            formal_result=None,
        )

    netlist_path = Path(cwd) / _NETLIST_FILENAME
    candidate_synth_result = synthesize(
        candidate_path,
        top_module=ALLOWED_TOP_MODULE,
        cwd=cwd,
        limits=limits,
        netlist_path=netlist_path,
    )
    if not candidate_synth_result.ok:
        return EvaluationResult(
            passed=False,
            stage="synthesize",
            policy_result=policy_result,
            simulate_result=sim_result,
            candidate_synth_result=candidate_synth_result,
            netlist_simulate_result=None,
            formal_result=None,
        )

    simcells_path = find_simcells_v()
    if simcells_path is None:
        raise RuntimeError(
            "could not locate yosys's simcells.v; required to re-simulate the "
            "synthesized netlist (see synthesize.find_simcells_v)"
        )

    netlist_sim_result = simulate(
        netlist_path,
        reference_path,
        test_path,
        cwd=cwd,
        limits=_with_netlist_output_floor(limits),
        extra_sources=(simcells_path,),
    )
    if not netlist_sim_result.passed:
        return EvaluationResult(
            passed=False,
            stage="netlist_simulate",
            policy_result=policy_result,
            simulate_result=sim_result,
            candidate_synth_result=candidate_synth_result,
            netlist_simulate_result=netlist_sim_result,
            formal_result=None,
        )

    formal_result = check_equivalence(candidate_path, reference_path, cwd=cwd, limits=limits)

    return EvaluationResult(
        passed=True,
        stage="done",
        policy_result=policy_result,
        simulate_result=sim_result,
        candidate_synth_result=candidate_synth_result,
        netlist_simulate_result=netlist_sim_result,
        formal_result=formal_result,
    )
