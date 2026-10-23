"""Real pass@k over independently-generated samples.

Unlike run_experiments.py's "pipeline sanity checks" (a few hand-written
attempts), this evaluates many independently generated samples per task
and reports the unbiased pass@k estimator from Chen et al. (2021):

    pass@k = 1 - C(n - c, k) / C(n, k)

where n is the number of samples per task, c is the number that passed,
and C is the binomial coefficient. Samples are read from
runs/real_pass_at_k/samples/<task_id>/sample_*.sv -- this script only
evaluates them; it does not generate them (see
runs/real_pass_at_k/GENERATION.md for how they were produced).

Writes runs/real_pass_at_k/results.json and prints a markdown table.
"""

from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path

from rtl_reward_lab.env import RTLRewardEnv
from rtl_reward_lab.tasks import Task

REPO_ROOT = Path(__file__).resolve().parents[1]
VERILOG_EVAL_DIR = REPO_ROOT / "third_party" / "verilog-eval" / "dataset_spec-to-rtl"
SAMPLES_ROOT = REPO_ROOT / "runs" / "real_pass_at_k" / "samples"

TASK_IDS = [
    "Prob003_step_one", "Prob005_notgate", "Prob009_popcount3", "Prob014_andgate",
    "Prob022_mux2to1", "Prob024_hadd", "Prob027_fadd", "Prob030_popcount255",
    "Prob050_kmap1", "Prob069_truthtable1", "Prob031_dff", "Prob034_dff8",
    "Prob040_count10", "Prob046_dff8p", "Prob063_review2015_shiftcount",
    "Prob068_countbcd", "Prob082_lfsr32", "Prob079_fsm3onehot", "Prob109_fsm1",
    "Prob128_fsm_ps2",
]


def _task(task_id: str) -> Task:
    return Task(
        id=task_id,
        prompt_path=VERILOG_EVAL_DIR / f"{task_id}_prompt.txt",
        reference_path=VERILOG_EVAL_DIR / f"{task_id}_ref.sv",
        test_path=VERILOG_EVAL_DIR / f"{task_id}_test.sv",
    )


def _pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased pass@k estimator (Chen et al., 2021, eq. 1)."""

    if n - c < k:
        return 1.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def run_task(task_id: str) -> dict:
    task = _task(task_id)
    env = RTLRewardEnv(task)
    sample_dir = SAMPLES_ROOT / task_id
    samples = []
    for sample_path in sorted(sample_dir.glob("sample_*.sv")):
        step_result = env.step(sample_path.read_text())
        samples.append(
            {
                "sample": sample_path.name,
                "passed": step_result.passed,
                "reward": step_result.reward,
                "stage": step_result.info["stage"],
            }
        )
    n = len(samples)
    c = sum(1 for s in samples if s["passed"])
    return {
        "samples": samples,
        "n": n,
        "c": c,
        "pass_at_1": _pass_at_k(n, c, 1) if n else None,
        "pass_at_k_full": _pass_at_k(n, c, n) if n else None,
    }


def main() -> None:
    results = {}
    for task_id in TASK_IDS:
        sample_dir = SAMPLES_ROOT / task_id
        if not sample_dir.is_dir() or not any(sample_dir.glob("sample_*.sv")):
            print(f"skipping {task_id}: no samples found in {sample_dir}")
            continue
        results[task_id] = run_task(task_id)

    out_path = REPO_ROOT / "runs" / "real_pass_at_k" / "results.json"
    out_path.write_text(json.dumps(results, indent=2))

    print(f"## Real pass@k (n={next(iter(results.values()))['n'] if results else '?'} samples/task)\n")
    print("| task | n | c | pass@1 |")
    print("| --- | --- | --- | --- |")
    total_n = total_c = 0
    pass_at_1_sum = 0.0
    for task_id, data in results.items():
        total_n += data["n"]
        total_c += data["c"]
        pass_at_1_sum += data["pass_at_1"] or 0.0
        print(f"| {task_id} | {data['n']} | {data['c']} | {data['pass_at_1']:.3f} |")

    if results:
        print(f"\nMean pass@1 across {len(results)} tasks: {pass_at_1_sum / len(results):.3f}")
        print(f"Overall: {total_c}/{total_n} samples passed")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
