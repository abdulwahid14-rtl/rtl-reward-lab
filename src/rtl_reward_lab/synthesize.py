"""Run a fixed Yosys flow and extract metrics."""

from __future__ import annotations

import dataclasses
import re
import shutil
from pathlib import Path

from rtl_reward_lab.reward import SynthesisMetrics
from rtl_reward_lab.runner import RunLimits, RunResult, run

_CELL_COUNT_RE = re.compile(r"Number of cells:\s+(\d+)")
_LONGEST_PATH_RE = re.compile(r"Longest topological path in \S+ \(length=(\d+)\)")


def find_simcells_v() -> Path | None:
    """Locate Yosys's `simcells.v`, the behavioral Verilog models for its
    internal gate primitives ($_AND_, $_DFFE_PN0P_, etc).

    Needed to simulate a Yosys-written netlist with Icarus Verilog: a
    netlist written by `write_verilog` after `synth` is expressed in terms
    of these internal cells, which are not standard Verilog and have no
    behavior of their own without this file alongside them.
    """

    yosys_bin = shutil.which("yosys")
    if yosys_bin is None:
        return None
    # Standard FHS layout: <prefix>/bin/yosys -> <prefix>/share/yosys/simcells.v
    candidate = Path(yosys_bin).resolve().parent.parent / "share" / "yosys" / "simcells.v"
    return candidate if candidate.is_file() else None


@dataclasses.dataclass(frozen=True)
class SynthesizeResult:
    """Outcome of running the fixed Yosys flow on a single RTL source."""

    ok: bool
    metrics: SynthesisMetrics | None
    run_result: RunResult


def synthesize(
    source_path: str | Path,
    *,
    top_module: str,
    cwd: str | Path,
    limits: RunLimits | None = None,
    netlist_path: str | Path | None = None,
) -> SynthesizeResult:
    """Run a fixed synth + stat + ltp flow over a single source file and
    extract its cell count and logic depth.

    The flow (`synth -top <module>; flatten; stat; ltp`) is intentionally
    fixed so that cell count and logic depth are comparable across
    candidates and the reference implementation.

    Two things make naive regex extraction wrong here, both handled below:

    1. `flatten` is required: without it, our own `stat` call reports
       per-module statistics, so a hierarchical design's top-level section
       only counts one "cell" per submodule instance (not that submodule's
       internal cells).
    2. `synth` itself prints its own internal, pre-flatten, per-module stat
       report as part of its normal flow, *before* our explicit `stat`
       command ever runs. That means stdout contains multiple "Number of
       cells:" lines, and the first one belongs to synth's own report, not
       ours. We take the *last* match of each metric so we read our final,
       post-flatten `stat`/`ltp` instead of synth's internal one.

    If `netlist_path` is given, the flattened, synthesized netlist is also
    written there with `write_verilog`. This is the design that is actually
    measured for cell count/depth; evaluator.py re-simulates it (rather than
    the original source) against the trusted testbench so that whatever
    synthesis produces is also what gets functionally checked -- otherwise
    a candidate could present different behavior to the simulator and the
    synthesizer (e.g. via a `SYNTHESIS`-guarded `` `ifdef ``, which Yosys
    defines by default and Icarus does not) and collect a reward for a
    design that was never actually verified.
    """

    script = f'read_verilog -sv "{source_path}"; synth -top {top_module}; flatten; stat; ltp'
    if netlist_path is not None:
        script += f'; write_verilog -noattr "{netlist_path}"'
    run_result = run(["yosys", "-p", script], cwd=cwd, limits=limits)

    if run_result.timed_out or run_result.returncode != 0:
        return SynthesizeResult(ok=False, metrics=None, run_result=run_result)

    cell_matches = _CELL_COUNT_RE.findall(run_result.stdout)
    depth_matches = _LONGEST_PATH_RE.findall(run_result.stdout)
    if not cell_matches or not depth_matches:
        return SynthesizeResult(ok=False, metrics=None, run_result=run_result)

    metrics = SynthesisMetrics(
        cell_count=int(cell_matches[-1]),
        logic_depth=int(depth_matches[-1]),
    )
    return SynthesizeResult(ok=True, metrics=metrics, run_result=run_result)
