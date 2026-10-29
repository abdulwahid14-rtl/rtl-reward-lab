import shutil
from pathlib import Path

import pytest

from rtl_reward_lab.evaluator import evaluate
from rtl_reward_lab.simulate import simulate
from rtl_reward_lab.synthesize import synthesize
from rtl_reward_lab.tools import (
    FLOWS,
    SIMULATORS,
    get_flow,
    get_simulator,
    liberty_flow,
    netlist_simulator,
)

MINI_LIB = Path(__file__).parent / "fixtures" / "mini.lib"

needs_verilator = pytest.mark.skipif(
    not SIMULATORS["verilator"].available(), reason="verilator not installed"
)


def test_unknown_simulator_and_flow_are_rejected():
    with pytest.raises(ValueError):
        get_simulator("modelsim")
    with pytest.raises(ValueError):
        get_flow("vivado")


def test_vendor_flow_netlist_falls_back_to_icarus_for_verilator():
    # Verilator can't parse Yosys's vendor cells_sim.v, so those netlists
    # must be re-simulated with Icarus, not skipped.
    assert netlist_simulator("verilator", FLOWS["ice40"]).name == "iverilog"
    assert netlist_simulator("verilator", FLOWS["generic"]).name == "verilator"
    assert netlist_simulator("iverilog", FLOWS["ice40"]).name == "iverilog"


@pytest.mark.parametrize("simulator", sorted(SIMULATORS))
def test_correct_candidate_passes_every_simulator(work_dir, simulator):
    if not SIMULATORS[simulator].available():
        pytest.skip(f"{simulator} not installed")

    result = simulate("candidate.sv", "reference.sv", "official_test.sv", cwd=work_dir, simulator=simulator)

    assert result.passed
    assert result.mismatches == 0
    assert result.total_samples == 220


@pytest.mark.parametrize("simulator", sorted(SIMULATORS))
def test_wrong_candidate_fails_every_simulator(work_dir, wrong_candidate_source, simulator):
    if not SIMULATORS[simulator].available():
        pytest.skip(f"{simulator} not installed")
    (work_dir / "wrong.sv").write_text(wrong_candidate_source)

    result = simulate("wrong.sv", "reference.sv", "official_test.sv", cwd=work_dir, simulator=simulator)

    assert not result.passed
    assert result.mismatches and result.mismatches > 0


@needs_verilator
def test_verilator_rebuild_in_same_dir_is_not_stale(work_dir, wrong_candidate_source):
    first = simulate("candidate.sv", "reference.sv", "official_test.sv", cwd=work_dir, simulator="verilator")
    shutil.copy(work_dir / "candidate.sv", work_dir / "good.sv")
    (work_dir / "candidate.sv").write_text(wrong_candidate_source)
    second = simulate("candidate.sv", "reference.sv", "official_test.sv", cwd=work_dir, simulator="verilator")

    assert first.passed
    assert not second.passed


@pytest.mark.parametrize("flow", sorted(FLOWS))
def test_every_flow_synthesizes_with_positive_metrics(work_dir, flow):
    result = synthesize("candidate.sv", top_module="TopModule", cwd=work_dir, flow=flow)

    assert result.ok
    assert result.metrics.cell_count > 0
    assert result.metrics.logic_depth > 0


@pytest.mark.parametrize("flow", sorted(FLOWS))
def test_every_flow_netlist_is_resimulated_and_passes(work_dir, flow):
    # evaluate() runs the netlist gate for whichever flow is chosen.
    result = evaluate(
        "candidate.sv", "reference.sv", "official_test.sv", cwd=work_dir, flow=flow
    )

    assert result.passed, result.stage
    assert result.netlist_simulate_result.passed


@needs_verilator
@pytest.mark.parametrize("flow", sorted(FLOWS))
def test_verilator_with_every_flow_passes_full_pipeline(work_dir, flow):
    result = evaluate(
        "candidate.sv", "reference.sv", "official_test.sv", cwd=work_dir,
        simulator="verilator", flow=flow,
    )

    assert result.passed, result.stage


def test_liberty_flow_reports_library_area(work_dir):
    result = synthesize("candidate.sv", top_module="TopModule", cwd=work_dir, flow=liberty_flow(MINI_LIB))

    assert result.ok, result.run_result.stderr[-500:]
    assert result.metrics.area is not None and result.metrics.area > 0
    # ltp can't see through Liberty cells, so depth is reported as unmeasured.
    assert result.metrics.logic_depth == 0


def test_liberty_flow_is_rejected_by_evaluate_instead_of_skipping_the_gate(work_dir, monkeypatch):
    monkeypatch.setenv("RTL_REWARD_LIBERTY", str(MINI_LIB))

    with pytest.raises(ValueError, match="cannot be"):
        evaluate("candidate.sv", "reference.sv", "official_test.sv", cwd=work_dir, flow="liberty")


def test_liberty_flow_needs_a_library_path(monkeypatch):
    monkeypatch.delenv("RTL_REWARD_LIBERTY", raising=False)

    with pytest.raises(ValueError, match="RTL_REWARD_LIBERTY"):
        get_flow("liberty")
