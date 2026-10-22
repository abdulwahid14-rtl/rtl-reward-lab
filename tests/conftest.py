import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
POPCOUNT3_DIR = REPO_ROOT / "examples" / "correct" / "popcount3"


@pytest.fixture
def popcount3_dir() -> Path:
    """The real, already-verified popcount3 example: candidate/reference/test .sv files."""

    return POPCOUNT3_DIR


@pytest.fixture
def work_dir(tmp_path: Path, popcount3_dir: Path) -> Path:
    """A scratch copy of the popcount3 example so tests can write compiler
    artifacts (simulation.vvp, wave.vcd) without touching the repo."""

    for name in ("candidate.sv", "reference.sv", "official_test.sv"):
        shutil.copy(popcount3_dir / name, tmp_path / name)
    return tmp_path


@pytest.fixture
def wrong_candidate_source() -> str:
    """A candidate that always outputs 0 -- functionally wrong for popcount3."""

    return (
        "module TopModule(input [2:0] in, output [1:0] out);\n"
        "  assign out = 2'b00;\n"
        "endmodule\n"
    )
