# rtl-reward-lab

I built this to explore a simple question: can a model get a good RTL score without producing correct hardware?

The project evaluates generated Verilog/SystemVerilog using Icarus Verilog and Yosys. Designs get a cell-count and logic-depth reward only after passing functional checks. It exposes an RL-style `reset()`/`step()` interface, but it doesn't train a model.

## How it works

1. Check the candidate against the submission rules.
2. Simulate it against the reference using the task's testbench.
3. Synthesize it with Yosys, then simulate the synthesized netlist too.
4. Score passing designs relative to the reference's cell count and depth.

Tasks include a population counter from [VerilogEval](https://github.com/NVlabs/verilog-eval) and a custom polyphase FIR filter.

## What I found

Testing the evaluator uncovered three ways to get undeserved rewards:

- Print a fake testbench pass message.
- Use different logic for simulation and synthesis.
- Read the testbench reference's output instead of computing it.

The current pipeline rejects these examples through submission checks and synthesized-netlist simulation. The attacks, fixes, and remaining gaps are documented in [reward-design.md](docs/reward-design.md).

A sample study recorded 168 passing submissions out of 200 across 20 VerilogEval tasks. The [generation notes](runs/real_pass_at_k/GENERATION.md) explain the setup and its limitations; this isn't evidence of model training or improvement.

## Run it

Requires Python 3.10+, Git, Icarus Verilog (`iverilog`/`vvp`), and Yosys on `PATH`.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pytest
./scripts/setup_verilog_eval.sh
python3 -m pytest -q
```

Re-evaluate the committed samples and reproduce the reward-hacking experiments:

```bash
python3 scripts/run_real_pass_at_k.py
python3 scripts/run_experiments.py
```

## Limitations

Passing simulation isn't a proof of correctness. Formal equivalence currently runs as a diagnostic, not an acceptance requirement, and sequential checking needs more work. Cell count and logic depth are proxies, not physical area or timing. This is a research prototype, not a secure sandbox for hostile submissions.

Next up: better sequential equivalence checks, parser-based submission rules, and feedback-driven repair experiments.

## Development

I designed the reward structure and experiments, and used Claude Code extensively for implementation and debugging.