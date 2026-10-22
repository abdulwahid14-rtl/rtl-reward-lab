from rtl_reward_lab.formal import check_equivalence


def test_correct_candidate_is_equivalent_to_reference(work_dir):
    result = check_equivalence("candidate.sv", "reference.sv", cwd=work_dir)

    assert result.equivalent


def test_wrong_candidate_is_not_equivalent_to_reference(work_dir, wrong_candidate_source):
    (work_dir / "candidate.sv").write_text(wrong_candidate_source)

    result = check_equivalence("candidate.sv", "reference.sv", cwd=work_dir)

    assert not result.equivalent
