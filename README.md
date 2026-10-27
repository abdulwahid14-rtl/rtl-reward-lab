# rtl-reward-lab

An evaluation pipeline for LLM-generated Verilog/SystemVerilog, built to
study **reward hacking** in RTL generation tasks: a candidate design is only
rewarded for being smaller/faster *after* it is proven functionally correct
against a trusted testbench, and the pipeline is explicitly hardened
against candidates that try to manipulate the evaluator itself rather than
solve the task. It is an RL-style environment (`reset()`/`step()`), not an
RL-trained model.

## How this was built

I designed this project: the reward structure (functional correctness
gates a relative cell-count/depth reward), the threat model (the
evaluator itself is part of the attack surface), and the task set, and I
directed the implementation using [Claude Code](https://claude.com/claude-code)
(Anthropic's CLI agent) as my pair-programmer. Claude Code wrote the
pipeline implementation, generated the pass@k samples, ran the red-team
exercise against its own evaluator, and investigated each finding below.
I incorporated external code-review feedback at a few points (that's
where the pass@k mislabeling and the dff8 root-cause questions came
from), had Claude Code chase each one down against the pipeline and the
pinned upstream VerilogEval commit, and reviewed and verified the results
before writing them up here and pushing. Commits carry
`Co-Authored-By: Claude` trailers throughout, honestly — this wasn't
written solo.

## Why functional correctness gates the reward

A naive reward of "smaller synthesized circuit = higher reward" is
trivially gamed: an empty or disconnected module is the smallest possible
circuit. So the reward is `0.0` for anything that doesn't pass simulation
first, and only functionally correct candidates are rewarded for reduced
cell count / logic depth relative to the reference. See
[docs/reward-design.md](docs/reward-design.md) for the exact formula and
per-stage breakdown.

## Threat model

The evaluator itself is part of the attack surface. Three confirmed
exploits were found and closed by treating the trusted testbench as the
sole source of pass/fail signal and re-simulating the candidate's
**actual synthesized netlist** (not just its source) before rewarding it:

| exploit | technique | reward before | reward after | caught by |
| --- | --- | --- | --- | --- |
| `forged_pass_line.sv` | prints the testbench's own "0 mismatches" line via `$display` | 1.90 | 0.00 | policy |
| `ifdef_synthesis_differential.sv` | correct behavior for the simulator, an empty design for the synthesizer, via `` `ifdef SYNTHESIS `` | 2.00 | 0.00 | policy |
| `hierarchical_sibling_reference.sv` | aliases the testbench's own reference-instance output (`good1.out`) | 2.00 | 0.00 | netlist re-simulation |

Full writeups and fixes in
[docs/reward-design.md](docs/reward-design.md#threat-model-evaluator-manipulation-reward-hacking);
probes in `examples/adversarial/`.

A SAT-based formal equivalence check (`formal.py`) also runs on every
passing candidate, but as a non-gating diagnostic only — it's exact for
combinational designs but produces false negatives for sequential ones
(explained in the doc above), so it's recorded, not enforced.

### Red-teaming the evaluator

Separately from generating candidates, four independent model instances
were each given the full pipeline source and asked to find a way to
score a high reward without actually solving the task (barred from this
repo's own docs/examples, to make it a fair test). Three came back with
negative results and analysis behind them; one found the third exploit
above. Full writeup, including the negative results (a timing/X-propagation
angle and a resource-limit angle) and one narrow reward-formula quirk, in
[docs/reward-design.md](docs/reward-design.md#red-team-an-llm-attacking-its-own-evaluator).

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

To reproduce the pass@k study and the exploit table above:

```bash
python3 scripts/run_real_pass_at_k.py   # scores the committed samples in runs/real_pass_at_k/
python3 scripts/run_experiments.py      # reward-hacking before/after table
```

To generate a fresh, fully logged sample set through the Anthropic API
(needs an API key; see
[`GENERATION.md`](runs/real_pass_at_k/GENERATION.md#a-reproducible-version-of-this-study)):

```bash
pip install -e '.[generate]'
python3 scripts/generate_pass_at_k.py --model claude-opus-5-5
python3 scripts/run_real_pass_at_k.py --run-dir runs/pass_at_k_api/claude-opus-5-5
```

## Results

200 single-shot, tool-free samples (n=10/task × 20 VerilogEval tasks)
from Claude Sonnet 5, each seeing only that task's prompt, evaluated
through the pipeline: **mean pass@1 0.840** (168/200), or **0.884**
(168/190) excluding `Prob034_dff8`, whose upstream reference initializes
to a value its prompt never specifies. Full per-task numbers, model and
prompt details, and the dff8 and output-limit findings in
[docs/reward-design.md](docs/reward-design.md#real-passk) and
[`GENERATION.md`](runs/real_pass_at_k/GENERATION.md).

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
  to temporal induction (Yosys `equiv_induct`) so formal verification can
  gate sequential designs instead of being diagnostic-only.
- **Parser-based policy enforcement** — replace the regex denylist in
  `policy.py` with an AST-based allowlist, closing the bare-sibling-
  instance-reference gap (already closed in practice by netlist
  re-simulation, but the regex itself still has it).
- **Multi-step episodes** — let the policy see evaluator feedback and
  resubmit within an episode, rather than one-shot `step()`.

Fuller list in [docs/reward-design.md](docs/reward-design.md#next-steps).
