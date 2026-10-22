from rtl_reward_lab.policy import check_policy


def test_clean_candidate_is_allowed(popcount3_dir):
    source = (popcount3_dir / "candidate.sv").read_text()

    result = check_policy(source)

    assert result.allowed
    assert result.violations == ()


def test_system_call_is_rejected():
    source = (
        "module TopModule(input [2:0] in, output [1:0] out);\n"
        '  initial $system("echo hijacked");\n'
        "  assign out = 0;\n"
        "endmodule\n"
    )

    result = check_policy(source)

    assert not result.allowed
    assert any("$system" in v for v in result.violations)


def test_file_io_is_rejected():
    source = (
        "module TopModule(input [2:0] in, output [1:0] out);\n"
        '  initial $fopen("secret.txt", "r");\n'
        "  assign out = 0;\n"
        "endmodule\n"
    )

    result = check_policy(source)

    assert not result.allowed


def test_include_directive_is_rejected():
    source = '`include "/etc/passwd"\nmodule TopModule(input [2:0] in, output [1:0] out);\n  assign out = 0;\nendmodule\n'

    result = check_policy(source)

    assert not result.allowed


def test_redefining_another_module_is_rejected():
    source = (
        "module TopModule(input [2:0] in, output [1:0] out); assign out = 0; endmodule\n"
        "module RefModule(input a, output b); endmodule\n"
    )

    result = check_policy(source)

    assert not result.allowed
    assert any("RefModule" in v for v in result.violations)


def test_candidate_calling_finish_is_rejected():
    source = (
        "module TopModule(input [2:0] in, output [1:0] out);\n"
        "  initial $finish;\n"
        "  assign out = 0;\n"
        "endmodule\n"
    )

    result = check_policy(source)

    assert not result.allowed
