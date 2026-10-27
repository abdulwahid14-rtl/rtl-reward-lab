from rtl_reward_lab.passk import TASK_IDS, build_prompt, extract_verilog, pass_at_k, task


def test_extract_takes_last_fenced_block():
    text = (
        "```verilog\nmodule TopModule(); // placeholder\nendmodule\n```\n"
        "Wait, here's the correct version:\n"
        "```systemverilog\nmodule TopModule(output one);\n  assign one = 1'b1;\nendmodule\n```"
    )

    assert extract_verilog(text) == "module TopModule(output one);\n  assign one = 1'b1;\nendmodule\n"


def test_extract_unfenced_text_is_returned_whole():
    text = "module TopModule(output one);\n  assign one = 1'b1;\nendmodule"

    assert extract_verilog(text) == text + "\n"


def test_prompt_contains_spec_and_dff_note_only_for_dff():
    plain = build_prompt("Prob005_notgate", "implement a NOT gate")
    dff = build_prompt("Prob031_dff", "implement a DFF")

    assert "implement a NOT gate" in plain
    assert "port directions" not in plain
    assert "port directions" in dff


def test_pass_at_k_matches_known_values():
    assert pass_at_k(10, 0, 1) == 0.0
    assert pass_at_k(10, 10, 1) == 1.0
    assert abs(pass_at_k(10, 5, 1) - 0.5) < 1e-12
    # With 9 failures out of 10, any 2 samples include the 1 pass with prob 1 - C(9,2)/C(10,2).
    assert abs(pass_at_k(10, 1, 2) - 0.2) < 1e-12


def test_every_task_has_upstream_files():
    for task_id in TASK_IDS:
        t = task(task_id)
        assert t.prompt_path.is_file()
        assert t.reference_path.is_file()
        assert t.test_path.is_file()
