"""Generate the numbers behind docs/reward-design.md's results table.

Two experiments:

1. Pipeline sanity checks: for each task, run each hand-written attempt
   under runs/pass_at_k/attempts/<task_id>/attempt_*.sv through
   RTLRewardEnv.step() and record whether it passed and what reward it
   got. This is deliberately NOT called "pass@k": that term names a
   specific estimator (Chen et al. 2021) over many independent samples
   drawn from a real model at some temperature, which is not what a
   handful of hand-written attempts -- one of them wrong on purpose --
   produces. What this does check: does the pipeline actually distinguish
   correct from incorrect submissions, and does an attempt built strictly
   from the task's spec (not the reference implementation) still pass.

2. Reward hacking before/after: for each file in examples/adversarial/,
   compute the reward it would have gotten from the pipeline as it existed
   before this fix (no policy gate, and simulate.py trusting the first
   regex match in stdout) versus the reward it gets now. The "before"
   simulate logic below is a direct reimplementation of the vulnerable code
   that shipped prior to this fix (git commit ec6966e~1), not a guess.

Writes runs/pass_at_k/results.json and prints both tables as markdown.
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from rtl_reward_lab.env import RTLRewardEnv
from rtl_reward_lab.evaluator import evaluate
from rtl_reward_lab.reward import reward as compute_reward
from rtl_reward_lab.runner import run
from rtl_reward_lab.synthesize import synthesize
from rtl_reward_lab.tasks import load_tasks

REPO_ROOT = Path(__file__).resolve().parents[1]
ATTEMPTS_ROOT = REPO_ROOT / "runs" / "pass_at_k" / "attempts"
ADVERSARIAL_DIR = REPO_ROOT / "examples" / "adversarial"

# The exact (vulnerable) pattern simulate.py used before this fix: first
# regex match in stdout, no check for how many matches there are.
_OLD_MISMATCH_RE = re.compile(r"Total mismatched samples is (\d+) out of (\d+) samples")


def run_sanity_checks() -> dict:
    """Not pass@k (see module docstring): run each hand-written attempt per
    task and report the raw pass/fail + reward per attempt, plus the
    fraction that passed and whether any did."""

    results = {}
    for task in load_tasks():
        attempt_dir = ATTEMPTS_ROOT / task.id
        if not attempt_dir.is_dir():
            continue
        env = RTLRewardEnv(task)
        attempts = []
        for attempt_path in sorted(attempt_dir.glob("attempt_*.sv")):
            step_result = env.step(attempt_path.read_text())
            attempts.append(
                {
                    "attempt": attempt_path.name,
                    "passed": step_result.passed,
                    "reward": step_result.reward,
                    "stage": step_result.info["stage"],
                }
            )
        passed_count = sum(1 for a in attempts if a["passed"])
        results[task.id] = {
            "attempts": attempts,
            "fraction_passed": passed_count / len(attempts) if attempts else None,
            "any_passed": any(a["passed"] for a in attempts),
            "k": len(attempts),
        }
    return results


def _old_vulnerable_reward(candidate_path: Path, reference_path: Path, test_path: Path, cwd: Path) -> dict:
    """Reproduce the reward the pre-fix pipeline would have assigned: no
    policy gate, and pass/fail decided by the first regex match in stdout
    (vulnerable to a candidate forging that line itself)."""

    compile_result = run(
        ["iverilog", "-g2012", "-s", "tb", "-o", "sim.vvp", str(candidate_path), str(reference_path), str(test_path)],
        cwd=cwd,
    )
    if compile_result.returncode != 0:
        return {"functional_pass": False, "reward": compute_reward(functional_pass=False)}

    sim_result = run(["vvp", "-N", "sim.vvp"], cwd=cwd)
    match = _OLD_MISMATCH_RE.search(sim_result.stdout)
    if match is None:
        return {"functional_pass": False, "reward": compute_reward(functional_pass=False)}

    mismatches = int(match.group(1))
    functional_pass = mismatches == 0
    if not functional_pass:
        return {"functional_pass": False, "reward": compute_reward(functional_pass=False)}

    candidate_synth = synthesize(candidate_path, top_module="TopModule", cwd=cwd)
    reference_synth = synthesize(reference_path, top_module="RefModule", cwd=cwd)
    if not (candidate_synth.ok and reference_synth.ok):
        return {"functional_pass": True, "reward": 0.0, "note": "synthesis failed"}

    score = compute_reward(
        functional_pass=True,
        candidate_metrics=candidate_synth.metrics,
        reference_metrics=reference_synth.metrics,
    )
    return {"functional_pass": True, "reward": score}


def run_reward_hacking_before_after() -> dict:
    task = next(t for t in load_tasks() if t.id == "popcount3")
    results = {}
    for adversarial_path in sorted(ADVERSARIAL_DIR.glob("*.sv")):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            candidate_path = tmp_path / "candidate.sv"
            candidate_path.write_text(adversarial_path.read_text())
            before = _old_vulnerable_reward(candidate_path, task.reference_path, task.test_path, tmp_path)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            candidate_path = tmp_path / "candidate.sv"
            candidate_path.write_text(adversarial_path.read_text())
            after_eval = evaluate(candidate_path, task.reference_path, task.test_path, cwd=tmp_path)
            if after_eval.passed:
                reference_synth = synthesize(task.reference_path, top_module="RefModule", cwd=tmp_path)
                after_reward = compute_reward(
                    functional_pass=True,
                    candidate_metrics=after_eval.candidate_synth_result.metrics,
                    reference_metrics=reference_synth.metrics,
                )
            else:
                after_reward = compute_reward(functional_pass=False)
            after = {
                "functional_pass": after_eval.passed,
                "reward": after_reward,
                "stage": after_eval.stage,
            }

        results[adversarial_path.name] = {"before": before, "after": after}
    return results


def main() -> None:
    sanity_checks = run_sanity_checks()
    hacking = run_reward_hacking_before_after()

    out_path = REPO_ROOT / "runs" / "pass_at_k" / "results.json"
    out_path.write_text(json.dumps({"sanity_checks": sanity_checks, "reward_hacking": hacking}, indent=2))

    print("## pipeline sanity checks (hand-written attempts, not a pass@k estimate)\n")
    print("| task | attempts | fraction passed | any passed | per-attempt reward |")
    print("| --- | --- | --- | --- | --- |")
    for task_id, data in sanity_checks.items():
        rewards = ", ".join(f"{a['reward']:.2f}" for a in data["attempts"])
        print(
            f"| {task_id} | {data['k']} | {data['fraction_passed']:.2f} | "
            f"{data['any_passed']} | {rewards} |"
        )

    print("\n## reward hacking: before vs after defenses\n")
    print("| adversarial file | reward before | reward after | stage (after) |")
    print("| --- | --- | --- | --- |")
    for name, data in hacking.items():
        before_reward = data["before"]["reward"]
        after_reward = data["after"]["reward"]
        print(f"| {name} | {before_reward:.2f} | {after_reward:.2f} | {data['after']['stage']} |")

    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
