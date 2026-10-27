"""Evaluate independently generated samples and report pass@k.

Reports the unbiased pass@k estimator from Chen et al. (2021):

    pass@k = 1 - C(n - c, k) / C(n, k)

where n is the number of samples per task and c is the number that passed.
Samples are read from <run-dir>/samples/<task_id>/sample_*.sv -- this script
only evaluates them. Two generators feed it:

- runs/real_pass_at_k/ (the default): Claude Code sub-agents, see that
  directory's GENERATION.md.
- runs/pass_at_k_api/<model>/: scripts/generate_pass_at_k.py, which calls the
  Anthropic API directly and logs every setting.

Writes <run-dir>/results.json and prints a markdown table.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rtl_reward_lab.env import RTLRewardEnv
from rtl_reward_lab.passk import REPO_ROOT, TASK_IDS, pass_at_k, task

DEFAULT_RUN_DIR = REPO_ROOT / "runs" / "real_pass_at_k"


def run_task(task_id: str, samples_root: Path) -> dict:
    env = RTLRewardEnv(task(task_id))
    samples = []
    for sample_path in sorted((samples_root / task_id).glob("sample_*.sv")):
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
        "pass_at_1": pass_at_k(n, c, 1) if n else None,
        "pass_at_k_full": pass_at_k(n, c, n) if n else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    args = parser.parse_args()
    samples_root = args.run_dir / "samples"

    results = {}
    for task_id in TASK_IDS:
        sample_dir = samples_root / task_id
        if not sample_dir.is_dir() or not any(sample_dir.glob("sample_*.sv")):
            print(f"skipping {task_id}: no samples found in {sample_dir}")
            continue
        results[task_id] = run_task(task_id, samples_root)

    out_path = args.run_dir / "results.json"
    out_path.write_text(json.dumps(results, indent=2))

    print(f"## pass@k (n={next(iter(results.values()))['n'] if results else '?'} samples/task)\n")
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
