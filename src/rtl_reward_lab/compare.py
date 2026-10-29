"""Run one candidate through every simulator and synthesis flow and report
where the tools agree or disagree.

This is a measurement harness, not a gate: evaluator.py is still what decides
a real episode. Here every (simulator) and every (flow) is run independently
so the results can be compared against each other.
"""

from __future__ import annotations

import dataclasses
import tempfile
from pathlib import Path

from rtl_reward_lab.policy import ALLOWED_TOP_MODULE, check_policy
from rtl_reward_lab.reward import SynthesisMetrics, reward
from rtl_reward_lab.runner import RunLimits
from rtl_reward_lab.simulate import simulate
from rtl_reward_lab.synthesize import synthesize
from rtl_reward_lab.tools import SIMULATORS, get_flow

_NETLIST = "_cmp_netlist.v"
# Netlists are re-simulated with Icarus here: it reads every flow's cell
# models and is fast, so a many-flow sweep isn't dominated by Verilator's
# C++ compile. Source-level agreement between simulators is measured
# separately, in `simulators`.
_NETLIST_SIMULATOR = "iverilog"


@dataclasses.dataclass(frozen=True)
class SimOutcome:
    passed: bool
    stage: str
    mismatches: int | None


@dataclasses.dataclass(frozen=True)
class FlowOutcome:
    """One synthesis flow's view of a candidate (and the reference)."""

    synthesized: bool
    netlist_passed: bool | None  # None: no cell models, so unverifiable
    candidate: SynthesisMetrics | None
    reference: SynthesisMetrics | None
    reward: float | None  # only when the source passed and the netlist is verified (or unverifiable)


@dataclasses.dataclass(frozen=True)
class Comparison:
    policy_ok: bool
    simulators: dict[str, SimOutcome]
    flows: dict[str, FlowOutcome]

    @property
    def simulators_agree(self) -> bool:
        return len({s.passed for s in self.simulators.values()}) <= 1


def compare_candidate(
    candidate_source: str,
    *,
    reference_path: str | Path,
    test_path: str | Path,
    simulators: list[str],
    flows: list[str],
    reference_top: str = "RefModule",
    limits: RunLimits | None = None,
) -> Comparison:
    policy_ok = check_policy(candidate_source).allowed
    if not policy_ok:
        return Comparison(policy_ok=False, simulators={}, flows={})

    with tempfile.TemporaryDirectory() as tmp:
        cwd = Path(tmp)
        (cwd / "candidate.sv").write_text(candidate_source)

        sim_outcomes: dict[str, SimOutcome] = {}
        for name in simulators:
            r = simulate("candidate.sv", reference_path, test_path, cwd=cwd, limits=limits, simulator=name)
            sim_outcomes[name] = SimOutcome(r.passed, r.stage, r.mismatches)
        source_passed = bool(sim_outcomes) and all(o.passed for o in sim_outcomes.values())

        flow_outcomes: dict[str, FlowOutcome] = {}
        for name in flows:
            flow = get_flow(name)
            cand = synthesize(
                "candidate.sv", top_module=ALLOWED_TOP_MODULE, cwd=cwd, limits=limits,
                netlist_path=cwd / _NETLIST, flow=flow,
            )
            ref = synthesize(reference_path, top_module=reference_top, cwd=cwd, limits=limits, flow=flow)
            if not (cand.ok and ref.ok):
                flow_outcomes[name] = FlowOutcome(False, None, None, None, None)
                continue

            netlist_passed: bool | None = None
            sim_lib = flow.sim_lib_path()
            if flow.verifiable() and sim_lib is not None:
                nr = simulate(
                    _NETLIST, reference_path, test_path, cwd=cwd, limits=limits,
                    extra_sources=(sim_lib,), simulator=_NETLIST_SIMULATOR,
                )
                netlist_passed = nr.passed

            scored = source_passed and netlist_passed is not False
            flow_outcomes[name] = FlowOutcome(
                synthesized=True,
                netlist_passed=netlist_passed,
                candidate=cand.metrics,
                reference=ref.metrics,
                reward=reward(
                    functional_pass=True, candidate_metrics=cand.metrics, reference_metrics=ref.metrics
                )
                if scored
                else 0.0,
            )

    return Comparison(policy_ok=True, simulators=sim_outcomes, flows=flow_outcomes)


def spearman(xs: list[float], ys: list[float]) -> float | None:
    """Spearman rank correlation (average ranks for ties); None if undefined."""

    n = len(xs)
    if n < 3 or n != len(ys):
        return None

    def ranks(values: list[float]) -> list[float]:
        order = sorted(range(n), key=lambda i: values[i])
        out = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and values[order[j + 1]] == values[order[i]]:
                j += 1
            for k in range(i, j + 1):
                out[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return out

    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = sum((a - mx) ** 2 for a in rx)
    vy = sum((b - my) ** 2 for b in ry)
    if vx == 0 or vy == 0:
        return None
    return cov / (vx * vy) ** 0.5


def available_simulators() -> list[str]:
    return [name for name, sim in SIMULATORS.items() if sim.available()]
