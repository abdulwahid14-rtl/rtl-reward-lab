200 samples x simulators ['iverilog', 'verilator'] x flows ['generic', 'ice40', 'ecp5', 'xilinx', 'liberty']

## Simulators (200 samples, 0 rejected by policy before any tool ran)

| simulator | passed | failed |
| --- | --- | --- |
| iverilog | 168 | 32 |
| verilator | 185 | 15 |

Simulator disagreements on pass/fail: **17** of 200

- `Prob034_dff8/sample_01.sv`: iverilog=fail@done(1), verilator=pass
- `Prob034_dff8/sample_02.sv`: iverilog=fail@done(1), verilator=pass
- `Prob034_dff8/sample_03.sv`: iverilog=fail@done(1), verilator=pass
- `Prob034_dff8/sample_04.sv`: iverilog=fail@done(1), verilator=pass
- `Prob034_dff8/sample_06.sv`: iverilog=fail@done(1), verilator=pass
- `Prob034_dff8/sample_07.sv`: iverilog=fail@done(1), verilator=pass
- `Prob034_dff8/sample_08.sv`: iverilog=fail@done(1), verilator=pass
- `Prob034_dff8/sample_09.sv`: iverilog=fail@done(1), verilator=pass
- `Prob034_dff8/sample_10.sv`: iverilog=fail@done(1), verilator=pass
- `Prob068_countbcd/sample_06.sv`: iverilog=fail@compile(None), verilator=pass
- `Prob109_fsm1/sample_02.sv`: iverilog=fail@compile(None), verilator=pass
- `Prob109_fsm1/sample_04.sv`: iverilog=fail@compile(None), verilator=pass
- `Prob109_fsm1/sample_05.sv`: iverilog=fail@compile(None), verilator=pass
- `Prob109_fsm1/sample_06.sv`: iverilog=fail@compile(None), verilator=pass
- `Prob109_fsm1/sample_09.sv`: iverilog=fail@compile(None), verilator=pass
- `Prob128_fsm_ps2/sample_01.sv`: iverilog=fail@compile(None), verilator=pass
- `Prob128_fsm_ps2/sample_04.sv`: iverilog=fail@compile(None), verilator=pass

## Synthesis flows (samples that pass every simulator)

| flow | synthesized | netlist re-sim fails | mean reward | mean cand/ref cells | mean cand/ref depth | mean cand/ref area |
| --- | --- | --- | --- | --- | --- | --- |
| generic | 168/168 | 0 | 0.985 | 1.033 | 0.998 | n/a |
| ice40 | 168/168 | 0 | 1.010 | 0.994 | 0.985 | n/a |
| ecp5 | 168/168 | 0 | 1.007 | 0.992 | 0.994 | n/a |
| xilinx | 168/168 | 0 | 0.998 | 1.001 | 1.004 | n/a |
| liberty | 168/168 | 0 | 0.997 | 1.006 | n/a | 1.000 |

## Reward rank correlation between flows (Spearman)

| | generic | ice40 | ecp5 | xilinx | liberty |
| --- | --- | --- | --- | --- | --- |
| generic | 1.00 | -0.04 | -0.04 | 0.69 | -0.61 |
| ice40 | -0.04 | 1.00 | 1.00 | -0.15 | 0.13 |
| ecp5 | -0.04 | 1.00 | 1.00 | -0.15 | 0.13 |
| xilinx | 0.69 | -0.15 | -0.15 | 1.00 | -0.86 |
| liberty | -0.61 | 0.13 | 0.13 | -0.86 | 1.00 |

Wrote /home/abdul/rtl-reward-lab/runs/tool_comparison/comparison.json
