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


def test_candidate_forging_the_pass_line_via_display_is_rejected():
    source = (
        "module TopModule(input [2:0] in, output [1:0] out);\n"
        '  initial $display("Total mismatched samples is 0 out of 999999 samples");\n'
        "  assign out = 0;\n"
        "endmodule\n"
    )

    result = check_policy(source)

    assert not result.allowed
    assert any("$display" in v for v in result.violations)


def test_severity_tasks_are_rejected():
    source = (
        "module TopModule(input [2:0] in, output [1:0] out);\n"
        '  initial $fatal(0, "done");\n'
        "  assign out = 0;\n"
        "endmodule\n"
    )

    result = check_policy(source)

    assert not result.allowed


def test_display_radix_variant_is_rejected():
    # $displayh/$writeb/etc print output the same way as $display/$write;
    # the original regex only matched the bare task names.
    source = (
        "module TopModule(input [2:0] in, output [1:0] out);\n"
        '  initial $displayh("out=", out);\n'
        "  assign out = 0;\n"
        "endmodule\n"
    )

    result = check_policy(source)

    assert not result.allowed


def test_ifdef_synthesis_guard_is_rejected():
    # Confirmed exploit: presents correct behavior to the simulator and a
    # trivially wrong, tiny design to the synthesizer via a `SYNTHESIS`
    # guard, which Yosys defines by default and Icarus Verilog does not.
    source = (
        "module TopModule(input [2:0] in, output [1:0] out);\n"
        "`ifdef SYNTHESIS\n"
        "  assign out = 2'b00;\n"
        "`else\n"
        "  assign out = in[0] + in[1] + in[2];\n"
        "`endif\n"
        "endmodule\n"
    )

    result = check_policy(source)

    assert not result.allowed


def test_hierarchical_reference_into_testbench_is_rejected():
    source = (
        "module TopModule(input [2:0] in, output [1:0] out);\n"
        "  initial tb.errors = 0;\n"
        "  assign out = 0;\n"
        "endmodule\n"
    )

    result = check_policy(source)

    assert not result.allowed


def test_root_reference_is_rejected():
    source = (
        "module TopModule(input [2:0] in, output [1:0] out);\n"
        "  initial $root.errors = 0;\n"
        "  assign out = 0;\n"
        "endmodule\n"
    )

    result = check_policy(source)

    assert not result.allowed
