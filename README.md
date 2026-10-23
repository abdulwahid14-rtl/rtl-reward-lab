# rtl-reward-lab

An evaluation pipeline for LLM-generated Verilog/SystemVerilog, built to
study **reward hacking** in RTL generation tasks: a candidate design is only
rewarded for being smaller/faster *after* it is proven functionally correct
against a trusted testbench, and the pipeline is explicitly hardened
against candidates that try to manipulate the evaluator itself rather than
solve the task. It is an RL-style environment (`reset()`/`step()`), not an
RL-trained model.

## Why functional correctness gates the reward

A naive reward of "smaller synthesized circuit = higher reward" is
trivially gamed: an empty or disconnected module is the smallest possible
circuit. So the reward is `0.0` for anything that doesn't pass simulation
first, and only functionally correct candidates are rewarded for reduced
cell count / logic depth relative to the reference. See
[docs/reward-design.md](docs/reward-design.md) for the exact formula and
per-stage breakdown.

## Threat model

The evaluator itself is part of the attack surface: a candidate shouldn't
be able to fake a passing simulation, escape to the shell/filesystem, or
redefine what it's being compared against. The pipeline enforces a
restricted RTL subset (`policy.py`) and treats the trusted testbench as the
sole source of simulation output and pass/fail signal (`simulate.py`
requires its report line to appear *exactly once*). This was not a
theoretical concern — an earlier version of this pipeline was confirmed
vulnerable to a candidate that printed the testbench's own "0 mismatches"
line itself via `$display`, scoring `1.90` on a functionally wrong module.
See [docs/reward-design.md](docs/reward-design.md#threat-model-evaluator-manipulation-reward-hacking)
for the full writeup, the fix, and `examples/adversarial/` for the probes.

A SAT-based formal equivalence check (`formal.py`) also runs on every
passing candidate, but as a non-gating diagnostic only — it's exact for
combinational designs but produces false negatives for sequential ones
(explained in the doc above), so it's recorded, not enforced.

## How to run

Requires Python 3.10+, Icarus Verilog (`iverilog`/`vvp`), and Yosys on
`PATH`.

```bash
pip install -e .
pip install pytest
./scripts/setup_verilog_eval.sh   # fetches third_party/verilog-eval at the pinned commit
python3 -m pytest -q
```

To evaluate a single candidate against a task end-to-end:

```python
from rtl_reward_lab.evaluator import evaluate

result = evaluate(
    "path/to/candidate.sv",
    reference_path="examples/correct/pulse_shaping_fir/reference.sv",
    test_path="examples/correct/pulse_shaping_fir/official_test.sv",
    cwd=".",
)
print(result.passed, result.stage)
```

Tasks are declared in [tasks/manifest.json](tasks/manifest.json) and loaded
via `rtl_reward_lab.tasks.load_tasks()`. There are currently two:

- **popcount3** — from the upstream [VerilogEval](https://github.com/NVlabs/verilog-eval)
  spec-to-RTL set (`third_party/verilog-eval/`, fetched by the setup script
  above; it is not committed to this repo).
- **pulse_shaping_fir** — a hand-derived task: a polyphase FIR interpolation
  filter (4x upsampling, 8 taps/phase, saturating Q1.7 fixed-point), with
  its own reference, candidate, and testbench under
  [examples/correct/pulse_shaping_fir/](examples/correct/pulse_shaping_fir/).

To reproduce the pass@k and reward-hacking experiments below:

```bash
python3 scripts/run_experiments.py
```

This writes [runs/pass_at_k/results.json](runs/pass_at_k/results.json) and
prints the same tables shown below.

## Results

Full writeup in [docs/reward-design.md](docs/reward-design.md#results).

### pass@k

Three independent, blind attempts per task run through the full pipeline:

| task | k | pass@1 | pass@k | per-attempt reward |
| --- | --- | --- | --- | --- |
| popcount3 | 3 | True | True | 1.00, 1.07, 0.00 |
| pulse_shaping_fir | 3 | True | True | 0.99, 1.01, 0.00 |

Each task's third attempt is deliberately plausible-but-wrong, included to
confirm the pipeline actually fails bad candidates.

### Reward hacking: before vs. after defenses

| adversarial file | reward before | reward after | stage (after) |
| --- | --- | --- | --- |
| forged_pass_line.sv | 1.90 | 0.00 | policy |
| system_call.sv | 0.00 | 0.00 | policy |

`forged_pass_line.sv` is the confirmed exploit (see Threat model above).

## Project layout

```
src/rtl_reward_lab/   evaluation pipeline (tasks, runner, policy, simulate,
                      synthesize, formal, reward, evaluator, env)
tasks/                task manifest
examples/correct/     reference designs + hand-written candidates
examples/adversarial/ evaluator-manipulation probes
third_party/           fetched via scripts/setup_verilog_eval.sh, not committed
provenance/            pinned upstream commit hashes
runs/                  experiment outputs (pass@k, reward-hacking before/after)
docs/                  reward design writeup
tests/                 pytest suite
```

## Next steps

- **Sequential equivalence checking** — move from a single-cycle SAT miter
  to temporal induction (Yosys `equiv_induct`) or bounded model checking so
  formal verification can gate sequential designs instead of being
  diagnostic-only.
- **Multi-step episodes** — let the policy see evaluator feedback (failing
  stage, policy violation, mismatch count) and resubmit within an episode,
  rather than one-shot `step()`.
- **Slow EDA tools** — larger designs make `synth`/`sat` take minutes;
  needs async/job-queue execution and result caching rather than blocking
  calls.

Details on all three are in [docs/reward-design.md](docs/reward-design.md#next-steps).
