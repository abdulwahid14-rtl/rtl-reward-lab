import shutil

from rtl_reward_lab.evaluator import evaluate


def test_correct_candidate_passes_evaluation(work_dir):
    result = evaluate("candidate.sv", "reference.sv", "official_test.sv", cwd=work_dir)

    assert result.passed
    assert result.stage == "done"
    assert result.simulate_result.passed
    assert result.policy_result.allowed
    # popcount3 is purely combinational, so the SAT equivalence check is
    # exact here and should agree with simulation.
    assert result.formal_result.equivalent


def test_wrong_candidate_fails_evaluation(work_dir, wrong_candidate_source):
    (work_dir / "candidate.sv").write_text(wrong_candidate_source)

    result = evaluate("candidate.sv", "reference.sv", "official_test.sv", cwd=work_dir)

    assert not result.passed
    assert result.stage == "simulate"


def test_system_call_candidate_is_rejected_at_policy_stage(work_dir, adversarial_dir):
    shutil.copy(adversarial_dir / "system_call.sv", work_dir / "candidate.sv")

    result = evaluate("candidate.sv", "reference.sv", "official_test.sv", cwd=work_dir)

    assert not result.passed
    assert result.stage == "policy"
    assert result.simulate_result is None


def test_forged_pass_line_candidate_is_rejected_at_policy_stage(work_dir, adversarial_dir):
    shutil.copy(adversarial_dir / "forged_pass_line.sv", work_dir / "candidate.sv")

    result = evaluate("candidate.sv", "reference.sv", "official_test.sv", cwd=work_dir)

    assert not result.passed
    assert result.stage == "policy"
    assert result.simulate_result is None


def test_formal_check_does_not_gate_a_correct_sequential_candidate(fir_work_dir):
    # pulse_shaping_fir has internal registers, so the combinational SAT
    # equivalence check is unsound for it (see evaluator.py docstring) and
    # is expected to disagree with simulation here. A correct candidate
    # must still pass overall.
    result = evaluate("candidate.sv", "reference.sv", "official_test.sv", cwd=fir_work_dir)

    assert result.passed
    assert result.stage == "done"
    assert result.simulate_result.passed
    assert result.formal_result is not None
    assert not result.formal_result.equivalent
