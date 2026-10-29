"""Compare simulators and synthesis flows over a set of candidate samples.

For every sample this runs each simulator on the candidate source and each
synthesis flow (plus netlist re-simulation), then reports:

- simulator agreement: samples where Icarus and Verilator disagree on pass/fail
- netlist-gate failures: samples that pass at source level but whose
  synthesized netlist fails re-simulation under some flow
- per-flow reward: how the reward moves with the mapping, and the rank
  correlation of rewards between flows

Samples are read from <run-dir>/samples/<task_id>/sample_*.sv, same layout as
run_real_pass_at_k.py. Writes <out-dir>/comparison.json and prints markdown.

    python3 scripts/compare_tools.py                      # committed 200 samples
    python3 scripts/compare_tools.py --tasks Prob034_dff8 # one task
    RTL_REWARD_LIBERTY=cells.lib python3 scripts/compare_tools.py --flows generic liberty
"""

from __future__ import annotations

import argparse
import dataclasses
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from rtl_reward_lab.compare import Comparison, available_simulators, compare_candidate, spearman
from rtl_reward_lab.passk import REPO_ROOT, TASK_IDS, task
from rtl_reward_lab.tools import available_flows

DEFAULT_RUN_DIR = REPO_ROOT / "runs" / "real_pass_at_k"
DEFAULT_OUT_DIR = REPO_ROOT / "runs" / "tool_comparison"


def _evaluate_sample(job: tuple[str, Path], simulators: list[str], flows: list[str]) -> tuple[str, str, Comparison]:
    task_id, path = job
    t = task(task_id)
    comparison = compare_candidate(
        path.read_text(),
        reference_path=t.reference_path,
        test_path=t.test_path,
        simulators=simulators,
        flows=flows,
    )
    return task_id, path.name, comparison


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--tasks", nargs="*", default=TASK_IDS)
    parser.add_argument("--simulators", nargs="*", default=available_simulators())
    parser.add_argument("--flows", nargs="*", default=available_flows())
    parser.add_argument("--jobs", type=int, default=8)
    args = parser.parse_args()

    samples_root = args.run_dir / "samples"
    jobs = [(tid, p) for tid in args.tasks for p in sorted((samples_root / tid).glob("sample_*.sv"))]
    print(f"{len(jobs)} samples x simulators {args.simulators} x flows {args.flows}", flush=True)

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        rows = list(pool.map(lambda j: _evaluate_sample(j, args.simulators, args.flows), jobs))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "comparison.json").write_text(
        json.dumps(
            [{"task": t, "sample": s, **dataclasses.asdict(c)} for t, s, c in rows], indent=2
        )
    )

    report(rows, args.simulators, args.flows)
    print(f"\nWrote {args.out_dir / 'comparison.json'}")


def report(rows: list[tuple[str, str, Comparison]], simulators: list[str], flows: list[str]) -> None:
    total = len(rows)
    policy_rejected = [r for r in rows if not r[2].policy_ok]
    live = [r for r in rows if r[2].policy_ok]

    print(f"\n## Simulators ({total} samples, {len(policy_rejected)} rejected by policy before any tool ran)\n")
    print("| simulator | passed | failed |")
    print("| --- | --- | --- |")
    for sim in simulators:
        passed = sum(1 for _, _, c in live if c.simulators[sim].passed)
        print(f"| {sim} | {passed} | {len(live) - passed} |")

    disagree = [r for r in live if not r[2].simulators_agree]
    print(f"\nSimulator disagreements on pass/fail: **{len(disagree)}** of {len(live)}\n")
    for task_id, sample, c in disagree:
        detail = ", ".join(f"{s}={'pass' if o.passed else f'fail@{o.stage}({o.mismatches})'}" for s, o in c.simulators.items())
        print(f"- `{task_id}/{sample}`: {detail}")

    print("\n## Synthesis flows (samples that pass every simulator)\n")
    agreed = [r for r in live if r[2].simulators and all(o.passed for o in r[2].simulators.values())]
    print("| flow | synthesized | netlist re-sim fails | mean reward | mean cand/ref cells | mean cand/ref depth | mean cand/ref area |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    per_flow_rewards: dict[str, dict[tuple[str, str], float]] = {f: {} for f in flows}
    for flow in flows:
        ok = [(t, s, c.flows[flow]) for t, s, c in agreed if c.flows[flow].synthesized]
        netlist_fail = [x for x in ok if x[2].netlist_passed is False]
        scored = [x for x in ok if x[2].reward is not None and x[2].netlist_passed is not False]
        for t, s, f in scored:
            per_flow_rewards[flow][(t, s)] = f.reward
        cells = [f.candidate.cell_count / f.reference.cell_count for _, _, f in scored if f.reference.cell_count]
        depth = [f.candidate.logic_depth / f.reference.logic_depth for _, _, f in scored if f.reference.logic_depth]
        areas = [
            f.candidate.area / f.reference.area
            for _, _, f in scored
            if f.candidate.area is not None and f.reference.area
        ]
        mean = lambda xs: f"{sum(xs) / len(xs):.3f}" if xs else "n/a"  # noqa: E731
        unverified = bool(ok) and all(x[2].netlist_passed is None for x in ok)
        print(
            f"| {flow} | {len(ok)}/{len(agreed)} | {'n/a (unverifiable)' if unverified else len(netlist_fail)} | "
            f"{mean([f.reward for _, _, f in scored])} | {mean(cells)} | {mean(depth)} | {mean(areas)} |"
        )
        for t, s, _ in netlist_fail:
            print(f"|  ↳ netlist fail: `{t}/{s}` | | | | | | |")

    if len(flows) > 1:
        print("\n## Reward rank correlation between flows (Spearman)\n")
        print("| | " + " | ".join(flows) + " |")
        print("| --- |" + " --- |" * len(flows))
        for a in flows:
            cells = []
            for b in flows:
                common = sorted(set(per_flow_rewards[a]) & set(per_flow_rewards[b]))
                rho = spearman([per_flow_rewards[a][k] for k in common], [per_flow_rewards[b][k] for k in common])
                cells.append("n/a" if rho is None else f"{rho:.2f}")
            print(f"| {a} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
