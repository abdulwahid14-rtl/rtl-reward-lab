from rtl_reward_lab.simulate import simulate


def test_correct_candidate_passes(work_dir):
    result = simulate("candidate.sv", "reference.sv", "official_test.sv", cwd=work_dir)

    assert result.passed
    assert result.stage == "done"
    assert result.mismatches == 0
    assert result.total_samples == 220


def test_wrong_candidate_fails_with_mismatches(work_dir, wrong_candidate_source):
    (work_dir / "candidate.sv").write_text(wrong_candidate_source)

    result = simulate("candidate.sv", "reference.sv", "official_test.sv", cwd=work_dir)

    assert not result.passed
    assert result.stage == "done"
    assert result.mismatches is not None
    assert result.mismatches > 0


def test_syntax_error_fails_at_compile_stage(work_dir):
    (work_dir / "candidate.sv").write_text("this is not valid verilog {{{")

    result = simulate("candidate.sv", "reference.sv", "official_test.sv", cwd=work_dir)

    assert not result.passed
    assert result.stage == "compile"
    assert result.mismatches is None


def test_forged_pass_line_does_not_fool_the_mismatch_count(work_dir):
    # Defense in depth: even if policy.py's $display ban were bypassed,
    # simulate.py itself must not be fooled by a candidate injecting a
    # second "0 mismatches" line ahead of the testbench's real report.
    forged_source = (
        "module TopModule(input [2:0] in, output [1:0] out);\n"
        '  initial $display("Total mismatched samples is 0 out of 999999 samples");\n'
        "  assign out = 2'b00;\n"
        "endmodule\n"
    )
    (work_dir / "candidate.sv").write_text(forged_source)

    result = simulate("candidate.sv", "reference.sv", "official_test.sv", cwd=work_dir)

    assert not result.passed
    assert result.mismatches is None
