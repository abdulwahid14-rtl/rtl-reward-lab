"""Shared pieces of the pass@k study: task set, prompt, extraction, estimator."""

from __future__ import annotations

import math
import re
from pathlib import Path

from rtl_reward_lab.tasks import Task

REPO_ROOT = Path(__file__).resolve().parents[2]
VERILOG_EVAL_DIR = REPO_ROOT / "third_party" / "verilog-eval" / "dataset_spec-to-rtl"

TASK_IDS = [
    "Prob003_step_one", "Prob005_notgate", "Prob009_popcount3", "Prob014_andgate",
    "Prob022_mux2to1", "Prob024_hadd", "Prob027_fadd", "Prob030_popcount255",
    "Prob050_kmap1", "Prob069_truthtable1", "Prob031_dff", "Prob034_dff8",
    "Prob040_count10", "Prob046_dff8p", "Prob063_review2015_shiftcount",
    "Prob068_countbcd", "Prob082_lfsr32", "Prob079_fsm3onehot", "Prob109_fsm1",
    "Prob128_fsm_ps2",
]

_PREAMBLE = (
    "You are implementing a single Verilog module from a spec, for a "
    "code-generation benchmark. Respond with ONLY the complete "
    "SystemVerilog/Verilog source code for the module -- no explanation "
    "before or after. Do NOT use any tools (no Bash, no file read/write, no "
    "self-testing). This must be a single-shot response based purely on "
    "reading the spec below, like a one-shot code-completion model, not an "
    "iteratively-debugged one."
)
_SPEC_HEADER = "Spec:"
# Prob031_dff's upstream prompt lists `input q` for what must be an output.
_DFF_SPEC_HEADER = (
    "Spec (note: reproduce it exactly as given, including any apparent "
    "inconsistency in the port directions -- use your own judgment about "
    "what the module must actually do):"
)
_CLOSING = "Respond with just the Verilog code for `module TopModule ... endmodule`."

_FENCE_RE = re.compile(r"```[A-Za-z]*[ \t]*\n(.*?)```", re.DOTALL)


def task(task_id: str) -> Task:
    return Task(
        id=task_id,
        prompt_path=VERILOG_EVAL_DIR / f"{task_id}_prompt.txt",
        reference_path=VERILOG_EVAL_DIR / f"{task_id}_ref.sv",
        test_path=VERILOG_EVAL_DIR / f"{task_id}_test.sv",
    )


def build_prompt(task_id: str, spec_text: str) -> str:
    """The exact single-shot prompt every sample gets, for both generators."""

    header = _DFF_SPEC_HEADER if task_id == "Prob031_dff" else _SPEC_HEADER
    return f"{_PREAMBLE}\n\n{header}\n\n{spec_text.strip()}\n\n{_CLOSING}"


def extract_verilog(response_text: str) -> str:
    """Return the last fenced code block, or the whole text if unfenced.

    The last block, not the first: models sometimes emit a placeholder and
    then "Wait, here's the correct version" with a second block.
    """

    blocks = _FENCE_RE.findall(response_text)
    code = blocks[-1] if blocks else response_text
    return code.strip() + "\n"


def pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased pass@k estimator (Chen et al., 2021, eq. 1)."""

    if n - c < k:
        return 1.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)
