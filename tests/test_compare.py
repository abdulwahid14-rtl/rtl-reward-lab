import pytest

from rtl_reward_lab.compare import available_simulators, compare_candidate, spearman


def test_spearman_perfect_and_inverse_and_degenerate():
    assert spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    assert spearman([1, 1, 1], [1, 2, 3]) is None  # constant input: undefined
    assert spearman([1, 2], [1, 2]) is None  # too few points


def test_spearman_handles_ties_with_average_ranks():
    assert spearman([1, 2, 2, 3], [1, 2, 2, 3]) == pytest.approx(1.0)


def test_policy_rejected_candidate_runs_no_tools(work_dir):
    result = compare_candidate(
        'module TopModule(input [2:0] in, output [1:0] out); initial $display("x"); endmodule',
        reference_path=work_dir / "reference.sv",
        test_path=work_dir / "official_test.sv",
        simulators=["iverilog"],
        flows=["generic"],
    )

    assert not result.policy_ok
    assert result.simulators == {} and result.flows == {}


def test_correct_candidate_agrees_across_tools_and_scores_one(work_dir):
    result = compare_candidate(
        (work_dir / "candidate.sv").read_text(),
        reference_path=work_dir / "reference.sv",
        test_path=work_dir / "official_test.sv",
        simulators=available_simulators(),
        flows=["generic", "ice40"],
    )

    assert result.simulators_agree
    assert all(o.passed for o in result.simulators.values())
    for flow in result.flows.values():
        assert flow.netlist_passed
        assert flow.reward == pytest.approx(1.0)


def test_wrong_candidate_scores_zero_in_every_flow(work_dir, wrong_candidate_source):
    result = compare_candidate(
        wrong_candidate_source,
        reference_path=work_dir / "reference.sv",
        test_path=work_dir / "official_test.sv",
        simulators=["iverilog"],
        flows=["generic", "ecp5"],
    )

    assert not any(o.passed for o in result.simulators.values())
    assert all(f.reward == 0.0 for f in result.flows.values())
