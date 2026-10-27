"""Dynamic-power proxy: count gate-output toggles for the reference and the
candidate of a task under the task's own testbench stimulus.

    python3 scripts/toggle_power_proxy.py [--task-dir examples/correct/pulse_shaping_fir]

Both designs are synthesized with Yosys (the same `synth; flatten` flow as
the reward), written out as gate-level netlists, and simulated together
under the official testbench with Yosys's simcells.v. A VCD of the testbench
is parsed and every transition on a cell-output net is counted, per design
(tb.dut = candidate, tb.ref_dut = reference).

This is a *relative* proxy, not power. There is no technology library, wire
load or glitch model: it only says which design switches more internal nets
for the same stimulus. The weighted figure uses an assumed capacitance of
(input pins + 1) per gate and 4 per flip-flop; change WEIGHTS to taste.
"""

from __future__ import annotations

import argparse
import collections
import re
import subprocess
import tempfile
from pathlib import Path

from rtl_reward_lab.passk import REPO_ROOT
from rtl_reward_lab.synthesize import find_simcells_v

DUMP_TB = (
    "module toggle_dump;\n"
    '  initial begin $dumpfile("toggles.vcd"); $dumpvars(0, tb); end\n'
    "endmodule\n"
)
_CELL_RE = re.compile(r"\\\$_(\w+?)_\s+(\S+)\s*(?:/\*.*?\*/)?\s*\((.*?)\);", re.DOTALL)
_PORT_RE = re.compile(r"\.(\w+)\(([^()]*)\)")
_OUT_PORTS = {"Y", "Q"}
FLOP_WEIGHT = 4


def _run(cmd: list[str], cwd: Path) -> str:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
    return result.stdout


def synth_netlist(source: Path, top: str, out: Path, cwd: Path) -> None:
    script = f'read_verilog -sv "{source}"; synth -top {top}; flatten; write_verilog -noattr -noexpr "{out}"'
    _run(["yosys", "-q", "-p", script], cwd)


def parse_cells(netlist: Path) -> list[tuple[str, str, int]]:
    """(cell type, output net, input pin count) for every Yosys primitive."""
    cells = []
    for kind, _name, body in _CELL_RE.findall(netlist.read_text()):
        ports = _PORT_RE.findall(body)
        outs = [net.strip() for pin, net in ports if pin in _OUT_PORTS]
        n_in = sum(1 for pin, _ in ports if pin not in _OUT_PORTS)
        if outs:
            cells.append((kind, outs[0], n_in))
    return cells


def _net_key(net: str) -> tuple[str, int]:
    net = net.strip().lstrip("\\").strip()
    m = re.match(r"^(.*?)\s*\[(\d+)\]$", net)
    return (m.group(1).strip(), int(m.group(2))) if m else (net, 0)


def count_toggles(vcd: Path):
    """(toggles per (scope path, name, bit), set of every declared bit)."""
    ids: dict[str, list[tuple[str, str, int]]] = {}  # vcd id -> [(scope, name, width)]
    scope: list[str] = []
    values: dict[str, str] = {}
    toggles: dict[tuple[str, str, int], int] = collections.Counter()
    declared: set[tuple[str, str, int]] = set()
    in_defs = True
    for line in vcd.read_text().splitlines():
        if in_defs:
            tok = line.split()
            if not tok:
                continue
            if tok[0] == "$scope":
                scope.append(tok[2])
            elif tok[0] == "$upscope":
                scope.pop()
            elif tok[0] == "$var":
                ids.setdefault(tok[3], []).append((".".join(scope), tok[4].lstrip("\\"), int(tok[2])))
            elif tok[0] == "$enddefinitions":
                in_defs = False
            continue
        if not line or line[0] in "#$":
            continue
        if line[0] in "01xzXZ":
            new, vid = line[0], line[1:]
        elif line[0] in "bB":
            new, vid = line[1:].split()
        else:
            continue
        old = values.get(vid)
        values[vid] = new
        if old is None:
            continue
        for scope_path, name, width in ids.get(vid, []):
            o, n = old.rjust(width, old[0] if old[0] in "xz" else "0"), new.rjust(width, new[0] if new[0] in "xz" else "0")
            for bit in range(width):
                a, b = o[width - 1 - bit], n[width - 1 - bit]
                if a != b and a in "01" and b in "01":  # ignore X->value at time 0
                    toggles[(scope_path, name, bit)] += 1
    return toggles, declared


def summarize(label: str, cells, toggles, declared, scope_path: str, cycles: int) -> dict:
    per_type: dict[str, int] = collections.Counter()
    total = weighted = matched = 0
    for kind, net, n_in in cells:
        name, bit = _net_key(net)
        key = (scope_path, name, bit)
        if key in declared:
            matched += 1
        t = toggles.get(key, 0)
        is_flop = kind.startswith("DFF")
        per_type["flop" if is_flop else "comb"] += t
        total += t
        weighted += t * (FLOP_WEIGHT if is_flop else n_in + 1)
    return {
        "label": label,
        "cells": len(cells),
        "matched": matched,
        "total": total,
        "comb": per_type["comb"],
        "flop": per_type["flop"],
        "weighted": weighted,
        "per_cell_cycle": total / len(cells) / cycles,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--task-dir", type=Path, default=REPO_ROOT / "examples/correct/pulse_shaping_fir")
    args = parser.parse_args()
    d = args.task_dir.resolve()

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        synth_netlist(d / "candidate.sv", "TopModule", tmp / "cand_net.v", tmp)
        synth_netlist(d / "reference.sv", "RefModule", tmp / "ref_net.v", tmp)
        (tmp / "dump.sv").write_text(DUMP_TB)
        _run(
            ["iverilog", "-g2012", "-s", "tb", "-s", "toggle_dump", "-o", "sim.vvp",
             "cand_net.v", "ref_net.v", str(d / "official_test.sv"), "dump.sv", str(find_simcells_v())],
            tmp,
        )
        out = _run(["vvp", "-N", "sim.vvp"], tmp)
        print(next((l for l in out.splitlines() if "mismatched" in l), "(no testbench report)"))
        cycles = int(re.search(r"out of (\d+) samples", out).group(1))
        toggles, declared = count_toggles(tmp / "toggles.vcd")
        rows = [
            summarize("reference", parse_cells(tmp / "ref_net.v"), toggles, declared, "tb.ref_dut", cycles),
            summarize("candidate", parse_cells(tmp / "cand_net.v"), toggles, declared, "tb.dut", cycles),
        ]

    print(f"\n| design | cells | nets found in VCD | total toggles | comb | flop | weighted | toggles/cell/cycle |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in rows:
        print(f"| {r['label']} | {r['cells']} | {r['matched']} | {r['total']} | {r['comb']} | {r['flop']} | "
              f"{r['weighted']} | {r['per_cell_cycle']:.3f} |")
    ref, cand = rows
    print(f"\ncandidate/reference: total {cand['total'] / ref['total']:.2f}x, weighted {cand['weighted'] / ref['weighted']:.2f}x")


if __name__ == "__main__":
    main()
