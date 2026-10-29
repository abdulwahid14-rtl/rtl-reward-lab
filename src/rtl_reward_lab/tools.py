"""Registry of the open-source simulators and synthesis flows the pipeline can use.

Everything here is data plus command construction; running the commands and
interpreting their output stays in simulate.py / synthesize.py so that the
trust-sensitive logic (exactly-one mismatch line, last-match metric
extraction) lives in one place regardless of which tool produced the output.
"""

from __future__ import annotations

import dataclasses
import os
import shutil
from pathlib import Path

DEFAULT_SIMULATOR = "iverilog"
DEFAULT_FLOW = "generic"

LIBERTY_ENV_VAR = "RTL_REWARD_LIBERTY"

_VERILATOR_MDIR = "_obj_verilator"


@dataclasses.dataclass(frozen=True)
class Simulator:
    """A Verilog simulator: how to build a testbench run and execute it.

    `reads_vendor_models` is whether the tool can parse Yosys's per-
    architecture simulation models (`ice40/cells_sim.v` etc). Those files
    use constructs Verilator rejects, so a netlist from a vendor flow is
    always re-simulated with a tool that can read them; see
    `netlist_simulator`.
    """

    name: str
    binary: str
    reads_vendor_models: bool

    def available(self) -> bool:
        return shutil.which(self.binary) is not None

    def build_commands(self, sources: list[str], compiled: str) -> tuple[list[str], list[str]]:
        """Return (compile_command, run_command) for `sources` with top `tb`."""

        if self.name == "iverilog":
            return (
                ["iverilog", "-g2012", "-s", "tb", "-o", compiled, *sources],
                ["vvp", "-N", compiled],
            )
        if self.name == "verilator":
            # --binary builds a standalone executable from the SystemVerilog
            # testbench (needs --timing for its `#` delays). Lint-class
            # warnings are not fatal: this is an evaluator, not a style gate,
            # and the testbench's own report line is still what decides pass/fail.
            return (
                [
                    "verilator", "--binary", "--timing", "-j", "2",
                    "-Wno-fatal", "-Wno-lint", "-Wno-style",
                    "--top-module", "tb", "-Mdir", _VERILATOR_MDIR, *sources,
                ],
                [f"./{_VERILATOR_MDIR}/Vtb"],
            )
        raise ValueError(f"unknown simulator {self.name!r}")

    def clean_build_dir(self, cwd: str | Path) -> None:
        """Verilator's make-based build reuses its output directory by
        timestamp, which can silently reuse stale objects when the same
        cwd is evaluated twice in a second; start each build clean."""

        if self.name == "verilator":
            shutil.rmtree(Path(cwd) / _VERILATOR_MDIR, ignore_errors=True)


SIMULATORS: dict[str, Simulator] = {
    "iverilog": Simulator("iverilog", "iverilog", reads_vendor_models=True),
    "verilator": Simulator("verilator", "verilator", reads_vendor_models=False),
}


def get_simulator(name: str) -> Simulator:
    try:
        return SIMULATORS[name]
    except KeyError:
        raise ValueError(f"unknown simulator {name!r}; choose from {sorted(SIMULATORS)}") from None


def netlist_simulator(requested: str, flow: "SynthFlow") -> Simulator:
    """The simulator to re-simulate `flow`'s netlist with: the requested one
    unless it can't read that flow's cell models, in which case Icarus."""

    sim = get_simulator(requested)
    if flow.vendor_models and not sim.reads_vendor_models:
        return SIMULATORS["iverilog"]
    return sim


def yosys_share_dir() -> Path | None:
    yosys_bin = shutil.which("yosys")
    if yosys_bin is None:
        return None
    # Standard FHS layout: <prefix>/bin/yosys -> <prefix>/share/yosys
    share = Path(yosys_bin).resolve().parent.parent / "share" / "yosys"
    return share if share.is_dir() else None


@dataclasses.dataclass(frozen=True)
class SynthFlow:
    """A fixed Yosys synthesis flow.

    All flows are driven by Yosys (it is the only mature open-source RTL
    synthesizer), but they differ in what actually decides the metrics:
    which technology mapper runs (generic gates vs. 4-input LUTs vs.
    Lattice/Xilinx primitives, or ABC against a Liberty cell library) and
    therefore how cell count and depth come out. Comparing them tells you
    how much of a reward is a property of the design vs. of one mapping.

    `sim_lib` is the Yosys-share-relative path of the behavioral models the
    written netlist needs to be re-simulated; None means no models exist
    (e.g. a Liberty flow, whose cells are whatever the library defines), so
    that flow's metrics cannot be netlist-verified.
    """

    name: str
    description: str
    commands: str  # Yosys commands after read_verilog; "{top}" is substituted
    sim_lib: str | None
    vendor_models: bool = False
    liberty: Path | None = None
    # Yosys's `ltp` can't trace paths through Liberty cells (they're opaque
    # blackboxes to it), so it reports a meaningless depth of 0 there. Such
    # flows report depth as unmeasured (0) and are judged on cells/area.
    measures_depth: bool = True

    def script(self, source_path: str | Path, top_module: str, netlist_path: str | Path | None) -> str:
        script = f'read_verilog -sv "{source_path}"; {self.commands.format(top=top_module)}; stat'
        if self.liberty is not None:
            script += f' -liberty "{self.liberty}"'
        if self.measures_depth:
            script += "; ltp"
        if netlist_path is not None:
            script += f'; write_verilog -noattr "{netlist_path}"'
        return script

    def sim_lib_path(self) -> Path | None:
        if self.sim_lib is None:
            return None
        share = yosys_share_dir()
        if share is None:
            return None
        path = share / self.sim_lib
        return path if path.is_file() else None

    def verifiable(self) -> bool:
        return self.sim_lib is not None


FLOWS: dict[str, SynthFlow] = {
    "generic": SynthFlow(
        "generic",
        "Yosys `synth` to generic gate cells (the original, default flow)",
        "synth -top {top}; flatten",
        "simcells.v",
    ),
    "ice40": SynthFlow(
        "ice40",
        "Yosys `synth_ice40`: 4-input LUTs + carry (Lattice iCE40)",
        "synth_ice40 -top {top}; flatten",
        "ice40/cells_sim.v",
        vendor_models=True,
    ),
    "ecp5": SynthFlow(
        "ecp5",
        "Yosys `synth_ecp5`: 4-input LUTs + carry (Lattice ECP5)",
        "synth_ecp5 -top {top}; flatten",
        "ecp5/cells_sim.v",
        vendor_models=True,
    ),
    "xilinx": SynthFlow(
        "xilinx",
        "Yosys `synth_xilinx`: 6-input LUTs + carry (Xilinx 7-series)",
        "synth_xilinx -top {top}; flatten",
        "xilinx/cells_sim.v",
        vendor_models=True,
    ),
}


def liberty_flow(liberty_path: str | Path) -> SynthFlow:
    """ABC technology mapping against a Liberty standard-cell library, with
    area reported from the library (`stat -liberty`) rather than just a
    cell count. Netlist cells are the library's, so there are no behavioral
    models to re-simulate with."""

    path = Path(liberty_path).resolve()
    return SynthFlow(
        "liberty",
        f"Yosys + ABC mapped to Liberty cells ({path.name}), library area reported",
        f'synth -top {{top}}; flatten; dfflibmap -liberty "{path}"; abc -liberty "{path}"; opt_clean',
        None,
        liberty=path,
        measures_depth=False,
    )


def get_flow(name: str) -> SynthFlow:
    if name == "liberty":
        lib = os.environ.get(LIBERTY_ENV_VAR)
        if not lib or not Path(lib).is_file():
            raise ValueError(f"flow 'liberty' needs ${LIBERTY_ENV_VAR} to point at a Liberty (.lib) file")
        return liberty_flow(lib)
    try:
        return FLOWS[name]
    except KeyError:
        raise ValueError(f"unknown flow {name!r}; choose from {sorted([*FLOWS, 'liberty'])}") from None


def available_flows() -> list[str]:
    """Flows usable in this environment (liberty only if its env var is set)."""

    names = list(FLOWS)
    lib = os.environ.get(LIBERTY_ENV_VAR)
    if lib and Path(lib).is_file():
        names.append("liberty")
    return names
