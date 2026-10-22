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
