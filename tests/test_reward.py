import pytest

from rtl_reward_lab.reward import SynthesisMetrics, reward


def test_functional_failure_always_scores_zero():
    assert reward(functional_pass=False) == 0.0


def test_functional_failure_scores_zero_even_with_tiny_candidate_metrics():
    tiny = SynthesisMetrics(cell_count=1, logic_depth=1)
    huge = SynthesisMetrics(cell_count=1000, logic_depth=100)

    assert reward(functional_pass=False, candidate_metrics=tiny, reference_metrics=huge) == 0.0


def test_passing_same_size_scores_base_reward():
    metrics = SynthesisMetrics(cell_count=5, logic_depth=3)

    assert reward(functional_pass=True, candidate_metrics=metrics, reference_metrics=metrics) == 1.0


def test_passing_smaller_candidate_scores_above_base():
    candidate = SynthesisMetrics(cell_count=3, logic_depth=1)
    reference = SynthesisMetrics(cell_count=5, logic_depth=2)

    assert reward(functional_pass=True, candidate_metrics=candidate, reference_metrics=reference) > 1.0


def test_passing_larger_candidate_scores_below_base():
    candidate = SynthesisMetrics(cell_count=10, logic_depth=4)
    reference = SynthesisMetrics(cell_count=5, logic_depth=2)

    assert reward(functional_pass=True, candidate_metrics=candidate, reference_metrics=reference) < 1.0


def test_reward_is_clamped_and_never_negative():
    candidate = SynthesisMetrics(cell_count=1000, logic_depth=1000)
    reference = SynthesisMetrics(cell_count=1, logic_depth=1)

    assert reward(functional_pass=True, candidate_metrics=candidate, reference_metrics=reference) == 0.0


def test_zero_valued_reference_metric_does_not_divide_by_zero():
    candidate = SynthesisMetrics(cell_count=0, logic_depth=0)
    reference = SynthesisMetrics(cell_count=0, logic_depth=0)

    assert reward(functional_pass=True, candidate_metrics=candidate, reference_metrics=reference) == 1.0


def test_missing_metrics_on_a_passing_result_is_an_error():
    with pytest.raises(ValueError):
        reward(functional_pass=True)
