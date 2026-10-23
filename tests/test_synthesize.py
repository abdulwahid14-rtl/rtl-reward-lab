from rtl_reward_lab.synthesize import find_simcells_v, synthesize


def test_candidate_synthesizes_with_expected_metrics(work_dir):
    result = synthesize("candidate.sv", top_module="TopModule", cwd=work_dir)

    assert result.ok
    assert result.metrics.cell_count == 5
    assert result.metrics.logic_depth == 3


def test_reference_synthesizes_with_same_metrics_as_candidate(work_dir):
    result = synthesize("reference.sv", top_module="RefModule", cwd=work_dir)

    assert result.ok
    assert result.metrics.cell_count == 5
    assert result.metrics.logic_depth == 3


def test_missing_source_file_fails_gracefully(tmp_path):
    result = synthesize("does_not_exist.sv", top_module="TopModule", cwd=tmp_path)

    assert not result.ok
    assert result.metrics is None


def test_wrong_top_module_name_fails_gracefully(work_dir):
    result = synthesize("candidate.sv", top_module="NoSuchModule", cwd=work_dir)

    assert not result.ok
    assert result.metrics is None


def test_netlist_path_writes_the_synthesized_design(work_dir):
    netlist_path = work_dir / "netlist.v"

    result = synthesize("candidate.sv", top_module="TopModule", cwd=work_dir, netlist_path=netlist_path)

    assert result.ok
    assert netlist_path.is_file()
    assert "TopModule" in netlist_path.read_text()


def test_find_simcells_v_locates_a_real_file():
    simcells_path = find_simcells_v()

    assert simcells_path is not None
    assert simcells_path.is_file()
    assert "simcells.v" in simcells_path.name
