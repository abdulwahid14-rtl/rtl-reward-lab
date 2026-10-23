from rtl_reward_lab.runner import RunLimits, run


def test_normal_command_succeeds(tmp_path):
    result = run(["echo", "hello"], cwd=tmp_path)

    assert result.returncode == 0
    assert result.stdout == "hello\n"
    assert not result.timed_out


def test_nonzero_exit_is_reported(tmp_path):
    result = run(["false"], cwd=tmp_path)

    assert result.returncode == 1
    assert not result.timed_out


def test_timeout_kills_the_process(tmp_path):
    result = run(["sleep", "5"], cwd=tmp_path, limits=RunLimits(timeout_seconds=0.3))

    assert result.timed_out
    assert result.returncode is None


def test_cpu_limit_terminates_a_busy_loop(tmp_path):
    busy_loop = "x = 0\nwhile True:\n    x += 1\n"
    (tmp_path / "busy.py").write_text(busy_loop)

    result = run(
        ["python3", "busy.py"],
        cwd=tmp_path,
        limits=RunLimits(timeout_seconds=10.0, cpu_seconds=1),
    )

    # Killed by the CPU rlimit (SIGXCPU) well before the 10s wall-clock timeout.
    assert not result.timed_out
    assert result.returncode != 0


def test_command_runs_in_the_given_cwd(tmp_path):
    (tmp_path / "marker.txt").write_text("found")

    result = run(["cat", "marker.txt"], cwd=tmp_path)

    assert result.returncode == 0
    assert result.stdout == "found"


def test_default_output_limit_allows_a_few_megabyte_file():
    # A longer-running trusted testbench can legitimately dump a multi-MB
    # VCD trace via $dumpvars even for a correct candidate (confirmed on a
    # real task: ~1.2 MB for a correct BCD counter). The old 1 MiB default
    # silently killed vvp mid-dump with SIGXFSZ, indistinguishable from a
    # real functional failure. Guard against that regressing.
    assert RunLimits().max_output_bytes >= 4 * 1024 * 1024


def test_file_write_past_the_limit_is_killed_by_sigxfsz(tmp_path):
    script = "f = open('out.bin', 'wb')\nf.write(b'0' * (3 * 1024 * 1024))\n"
    (tmp_path / "write_big.py").write_text(script)

    result = run(
        ["python3", "write_big.py"],
        cwd=tmp_path,
        limits=RunLimits(max_output_bytes=1024 * 1024),
    )

    assert not result.timed_out
    assert result.returncode != 0
