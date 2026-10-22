from rtl_reward_lab.evaluator import evaluate


def test_correct_candidate_passes_evaluation(work_dir):
    result = evaluate("candidate.sv", "reference.sv", "official_test.sv", cwd=work_dir)

    assert result.passed
    assert result.stage == "done"
    assert result.simulate_result.passed


def test_wrong_candidate_fails_evaluation(work_dir, wrong_candidate_source):
    (work_dir / "candidate.sv").write_text(wrong_candidate_source)

    result = evaluate("candidate.sv", "reference.sv", "official_test.sv", cwd=work_dir)

    assert not result.passed
    assert result.stage == "simulate"
