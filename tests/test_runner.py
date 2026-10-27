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
    assert RunLimits().max_file_bytes >= 4 * 1024 * 1024


def test_file_write_past_the_limit_is_killed_by_sigxfsz(tmp_path):
    script = "f = open('out.bin', 'wb')\nf.write(b'0' * (3 * 1024 * 1024))\n"
    (tmp_path / "write_big.py").write_text(script)

    result = run(
        ["python3", "write_big.py"],
        cwd=tmp_path,
        limits=RunLimits(max_file_bytes=1024 * 1024),
    )

    assert not result.timed_out
    assert result.returncode != 0


def test_stdout_flood_is_killed_and_capped(tmp_path):
    flood = "import sys\nwhile True:\n    sys.stdout.write('x' * 65536)\n"
    (tmp_path / "flood.py").write_text(flood)

    result = run(
        ["python3", "flood.py"],
        cwd=tmp_path,
        limits=RunLimits(timeout_seconds=10.0, max_log_bytes=1024 * 1024),
    )

    # Killed by the log cap, well before the wall-clock timeout, and the
    # parent kept no more than the cap.
    assert result.output_overflow
    assert not result.timed_out
    assert result.returncode != 0
    assert len(result.stdout) + len(result.stderr) <= 1024 * 1024


def test_log_cap_counts_stdout_and_stderr_together(tmp_path):
    # Each stream alone is under the cap; together they exceed it.
    script = (
        "import sys, time\n"
        "sys.stdout.write('o' * (600 * 1024)); sys.stdout.flush()\n"
        "sys.stderr.write('e' * (600 * 1024)); sys.stderr.flush()\n"
        "time.sleep(30)\n"
    )
    (tmp_path / "both.py").write_text(script)

    result = run(
        ["python3", "both.py"],
        cwd=tmp_path,
        limits=RunLimits(timeout_seconds=10.0, max_log_bytes=1024 * 1024),
    )

    assert result.output_overflow
    assert not result.timed_out


def test_file_and_log_limits_are_independent(tmp_path):
    # 3 MB to stdout passes a 1 MiB file cap (RLIMIT_FSIZE doesn't bind
    # pipes), and a 3 MB file passes a 1 MiB log cap.
    (tmp_path / "print_big.py").write_text("print('x' * (3 * 1024 * 1024))\n")
    (tmp_path / "write_big.py").write_text("open('out.bin', 'wb').write(b'0' * (3 * 1024 * 1024))\n")

    printed = run(["python3", "print_big.py"], cwd=tmp_path, limits=RunLimits(max_file_bytes=1024 * 1024))
    written = run(["python3", "write_big.py"], cwd=tmp_path, limits=RunLimits(max_log_bytes=1024 * 1024))

    assert printed.returncode == 0 and not printed.output_overflow
    assert len(printed.stdout) == 3 * 1024 * 1024 + 1
    assert written.returncode == 0 and not written.output_overflow
    assert (tmp_path / "out.bin").stat().st_size == 3 * 1024 * 1024


def test_timeout_still_applies_when_child_closes_its_pipes(tmp_path):
    script = "import os, time\nos.close(1)\nos.close(2)\ntime.sleep(5)\n"
    (tmp_path / "quiet.py").write_text(script)

    result = run(["python3", "quiet.py"], cwd=tmp_path, limits=RunLimits(timeout_seconds=0.5))

    assert result.timed_out
    assert result.returncode is None
