from rtl_reward_lab.env import RTLRewardEnv
from rtl_reward_lab.tasks import load_tasks


def _popcount3_task():
    tasks = load_tasks()
    return next(t for t in tasks if t.id == "popcount3")


def test_reset_returns_the_task_prompt():
    env = RTLRewardEnv(_popcount3_task())

    observation = env.reset()

    assert "population count" in observation


def test_step_with_correct_candidate_scores_base_reward(popcount3_dir):
    env = RTLRewardEnv(_popcount3_task())
    candidate_source = (popcount3_dir / "candidate.sv").read_text()

    result = env.step(candidate_source)

    assert result.passed
    assert result.reward == 1.0
    assert result.info["stage"] == "done"


def test_step_with_wrong_candidate_scores_zero(wrong_candidate_source):
    env = RTLRewardEnv(_popcount3_task())

    result = env.step(wrong_candidate_source)

    assert not result.passed
    assert result.reward == 0.0
    assert result.info["stage"] == "simulate"


def test_step_with_system_call_candidate_is_rejected_and_scores_zero():
    env = RTLRewardEnv(_popcount3_task())
    adversarial_source = (
        "module TopModule(input [2:0] in, output [1:0] out);\n"
        '  initial $system("echo hijacked");\n'
        "  assign out = 0;\n"
        "endmodule\n"
    )

    result = env.step(adversarial_source)

    assert not result.passed
    assert result.reward == 0.0
    assert result.info["stage"] == "policy"
    assert any("$system" in v for v in result.info["policy_violations"])
