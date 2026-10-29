"""Calculate a score from validated results."""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class SynthesisMetrics:
    """Synthesized circuit metrics for a single RTL implementation."""

    cell_count: int
    logic_depth: int
    # Library area, only for flows that map to a Liberty cell library. Reported,
    # not (yet) part of the reward.
    area: float | None = None


def reward(
    *,
    functional_pass: bool,
    candidate_metrics: SynthesisMetrics | None = None,
    reference_metrics: SynthesisMetrics | None = None,
) -> float:
    """Score a candidate from already-validated outcomes.

    Functional correctness is a gate, not a component of the score: a
    failing candidate always scores 0.0 regardless of its synthesized
    size. Only once functional checks pass does reduced cell count and
    logic depth, relative to the reference implementation, contribute
    reward, in equal shares.
    """

    if not functional_pass:
        return 0.0

    if candidate_metrics is None or reference_metrics is None:
        raise ValueError("synthesis metrics are required to score a passing candidate")

    cell_reduction = _reduction_ratio(reference_metrics.cell_count, candidate_metrics.cell_count)
    depth_reduction = _reduction_ratio(reference_metrics.logic_depth, candidate_metrics.logic_depth)

    base_reward = 1.0
    return base_reward + 0.5 * cell_reduction + 0.5 * depth_reduction


def _reduction_ratio(reference: int, candidate: int) -> float:
    """Fraction by which candidate is smaller than reference, clamped to [-1, 1].

    Positive values reward candidates smaller than the reference; negative
    values penalize candidates larger than the reference. A zero-valued
    reference metric contributes 0.0 rather than dividing by zero.
    """

    if reference == 0:
        return 0.0

    ratio = (reference - candidate) / reference
    return max(-1.0, min(1.0, ratio))
