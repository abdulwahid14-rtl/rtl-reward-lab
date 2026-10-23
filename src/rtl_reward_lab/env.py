"""Expose observations, actions, and rewards."""

from __future__ import annotations

import dataclasses
import tempfile
from pathlib import Path
from typing import Any

from rtl_reward_lab.evaluator import evaluate
from rtl_reward_lab.reward import reward as compute_reward
from rtl_reward_lab.synthesize import synthesize
from rtl_reward_lab.tasks import Task


@dataclasses.dataclass(frozen=True)
class StepResult:
    """Observation, reward, and diagnostic info produced by one step."""

    reward: float
    passed: bool
    info: dict[str, Any]


class RTLRewardEnv:
    """A single-task, single-step RL-style environment.

    `reset()` returns the task's natural-language prompt as the
    observation. `step(candidate_source)` takes one action -- a complete
    candidate RTL implementation as a string -- and returns the reward
    computed by running it through simulate -> evaluate -> synthesize ->
    reward, the same pipeline evaluator.py and reward.py already define.
    There is no multi-step interaction: each episode is exactly one
    action.
    """

    def __init__(self, task: Task) -> None:
        self._task = task

    def reset(self) -> str:
        """Return the task prompt as the initial observation."""

        return self._task.prompt_path.read_text()

    def step(self, candidate_source: str) -> StepResult:
        """Evaluate one candidate RTL submission and return its reward."""

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            candidate_path = tmp_path / "candidate.sv"
            candidate_path.write_text(candidate_source)

            eval_result = evaluate(
                candidate_path,
                self._task.reference_path,
                self._task.test_path,
                cwd=tmp_path,
            )
            if not eval_result.passed:
                info: dict[str, Any] = {"stage": eval_result.stage}
                if eval_result.policy_result is not None:
                    info["policy_violations"] = eval_result.policy_result.violations
                return StepResult(
                    reward=compute_reward(functional_pass=False),
                    passed=False,
                    info=info,
                )

            candidate_synth = eval_result.candidate_synth_result
            reference_synth = synthesize(
                self._task.reference_path, top_module="RefModule", cwd=tmp_path
            )
            if not (candidate_synth.ok and reference_synth.ok):
                return StepResult(
                    reward=0.0,
                    passed=True,
                    info={"stage": "synthesize", "error": "synthesis failed"},
                )

            score = compute_reward(
                functional_pass=True,
                candidate_metrics=candidate_synth.metrics,
                reference_metrics=reference_synth.metrics,
            )
            return StepResult(
                reward=score,
                passed=True,
                info={
                    "stage": "done",
                    "candidate_metrics": candidate_synth.metrics,
                    "reference_metrics": reference_synth.metrics,
                    "formal_equivalent": eval_result.formal_result.equivalent
                    if eval_result.formal_result is not None
                    else None,
                },
            )
