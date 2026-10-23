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
be able to fake a passing simulation, escape to the shell/filesystem,
redefine what it's being compared against, or present different behavior
to the tool that checks it than to the tool that rewards it. The pipeline
enforces a restricted RTL subset (`policy.py`), treats the trusted
testbench as the sole source of simulation output and pass/fail signal
(`simulate.py` requires its report line to appear *exactly once*), and
re-simulates the candidate's **actual synthesized netlist** — not just its
source — against that same testbench before rewarding it. None of this is
theoretical: two confirmed exploits were found and closed this way. One
printed the testbench's own "0 mismatches" line itself via `$display`,
scoring `1.90` on a functionally wrong module. The other presented correct
behavior to the simulator and a trivially wrong, empty design to the
synthesizer via an `` `ifdef SYNTHESIS `` guard (Yosys defines `SYNTHESIS`
by default; Icarus Verilog does not), scoring the maximum possible reward
of `2.0`, completely silently. See
[docs/reward-design.md](docs/reward-design.md#threat-model-evaluator-manipulation-reward-hacking)
for both writeups, the fixes, and `examples/adversarial/` for the probes.

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

To reproduce the sanity-check and reward-hacking experiments below:

```bash
python3 scripts/run_experiments.py
```

This writes [runs/pass_at_k/results.json](runs/pass_at_k/results.json) and
prints the same tables shown below.

## Results

Full writeup in [docs/reward-design.md](docs/reward-design.md#results).

### Pipeline sanity checks (not a pass@k estimate)

A handful of hand-written attempts per task, not samples from a real
model — see [docs/reward-design.md](docs/reward-design.md#pipeline-sanity-checks-not-a-passk-estimate)
for why this is deliberately not called pass@k, and what a real pass@k
study here would need.

| task | attempts | fraction passed | any passed | per-attempt reward |
| --- | --- | --- | --- | --- |
| popcount3 | 3 | 0.67 | True | 1.00, 1.07, 0.00 |
| pulse_shaping_fir | 4 | 0.75 | True | 0.99, 1.01, 0.00, 0.96 |

Each task includes a deliberately plausible-but-wrong attempt, confirming
the pipeline actually fails bad candidates. `pulse_shaping_fir`'s fourth
attempt was written from the task's text prompt alone, without looking at
the reference or the other hand-written candidate.

### Reward hacking: before vs. after defenses

| adversarial file | reward before | reward after | stage (after) |
| --- | --- | --- | --- |
| forged_pass_line.sv | 1.90 | 0.00 | policy |
| ifdef_synthesis_differential.sv | 2.00 | 0.00 | policy |
| system_call.sv | 0.00 | 0.00 | policy |

Both `forged_pass_line.sv` and `ifdef_synthesis_differential.sv` are
confirmed exploits (see Threat model above).

## Project layout

```
src/rtl_reward_lab/   evaluation pipeline (tasks, runner, policy, simulate,
                      synthesize, formal, reward, evaluator, env)
tasks/                task manifest
examples/correct/     reference designs + hand-written candidates
examples/adversarial/ evaluator-manipulation probes
third_party/           fetched via scripts/setup_verilog_eval.sh, not committed
provenance/            pinned upstream commit hashes
runs/                  experiment outputs (sanity checks, reward-hacking before/after)
docs/                  reward design writeup
tests/                 pytest suite
```

## Next steps

- **Sequential equivalence checking** — move from a single-cycle SAT miter
  to temporal induction (Yosys `equiv_induct`) or bounded model checking so
  formal verification can gate sequential designs instead of being
  diagnostic-only.
- **A real pass@k study** — sample 10–20 attempts per task from an actual
  model across 20+ VerilogEval problems and report the Chen et al. (2021)
  unbiased estimator, instead of today's hand-written sanity checks.
- **Parser-based policy enforcement** — replace the regex denylist in
  `policy.py` with an AST-based allowlist (e.g. via `pyslang` or
  Verilator's lint output), which a determined macro-based or
  comment/string-confusing candidate could in principle evade.
- **Multi-step episodes** — let the policy see evaluator feedback (failing
  stage, policy violation, mismatch count) and resubmit within an episode,
  rather than one-shot `step()`.
- **Slow EDA tools** — larger designs make `synth`/`sat` take minutes;
  needs async/job-queue execution and result caching rather than blocking
  calls.

Details on all of these are in [docs/reward-design.md](docs/reward-design.md#next-steps).
