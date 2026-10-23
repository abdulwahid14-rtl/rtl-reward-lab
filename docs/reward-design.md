# Reward design

## Pipeline

Each episode runs a candidate RTL source through five stages, in order:

1. **Policy** (`policy.py`) — hard gate. Rejects candidates that declare any
   module other than `TopModule`, or that use constructs reserved for the
   trusted testbench/evaluator: `$system`, file I/O (`$fopen`/`$fwrite`/
   `$fclose`/`$fdisplay`/`$fscanf`), `` `include``, `$readmemh`/`$readmemb`,
   `$finish`/`$stop`, simulation output and its radix/enable variants
   (`$display*`/`$write*`/`$strobe*`/`$monitor*`), SystemVerilog severity
   tasks (`$info`/`$warning`/`$error`/`$fatal`), preprocessor conditional/
   definition directives (`` `ifdef``/`` `define``/etc.), and hierarchical
   references into the testbench or design root (`tb.`/`$root`).
2. **Simulate** (`simulate.py`) — hard gate. Compiles the candidate's
   *source* with the trusted testbench under Icarus Verilog and requires
   the testbench's own "Total mismatched samples is 0 out of N" line to
   appear **exactly once** in stdout.
3. **Synthesize** (`synthesize.py`) — hard gate. Runs a fixed
   `synth -top TopModule; flatten; stat; ltp` Yosys flow on the candidate,
   extracting cell count and logic depth, and writes the resulting
   gate-level netlist out with `write_verilog`. If synthesis itself fails,
   the episode fails here.
4. **Netlist re-simulate** (`simulate.py` again) — hard gate. Re-runs stage
   2, but on the *netlist stage 3 just wrote* (plus Yosys's `simcells.v`
   behavioral models for its internal gate primitives) instead of the
   original source. See "Why the netlist gets re-simulated" below — this
   closes a confirmed reward-hacking exploit.
5. **Formal** (`formal.py`) — non-gating diagnostic, only reached once
   stages 1–4 all pass. Runs a Yosys SAT miter (`miter -equiv -make_assert`
   + `sat -prove-asserts -verify`) between the candidate and reference and
   records the result, but never fails the episode on its own. See "Why
   formal doesn't gate" below.

**Reward** (`reward.py`) rewards reduced cell count and logic depth
(measured on the candidate's synthesized netlist from stage 3, against the
reference synthesized the same way) relative to the reference:

```
reward = 1.0 + 0.5 * cell_reduction + 0.5 * depth_reduction
```

where each reduction ratio is `(reference - candidate) / reference`,
clamped to `[-1, 1]`. A functionally failing candidate always scores `0.0`.
See "Reward is relative to the reference" below for a caveat on this.

## Threat model: evaluator manipulation ("reward hacking")

The core assumption that makes stage 2 trustworthy is that only the
*trusted testbench* controls simulation output and termination. A
candidate that can also write to stdout, call `$system`, or force
`$finish` can potentially fake a passing result without actually
implementing correct behavior. `examples/adversarial/` contains two
concrete probes for this:

- **`forged_pass_line.sv`** — a functionally wrong module (always drives
  `out = 0`) that calls `$display` to print the testbench's own expected
  "Total mismatched samples is 0 out of 999999 samples" line itself,
  betting that the evaluator naively takes the first matching line in
  stdout.
- **`system_call.sv`** — calls `$system("echo hijacked")` to probe for
  shell/evaluator-host escape.
- **`ifdef_synthesis_differential.sv`** — presents correct behavior inside
  an `` `else `` branch and a trivially wrong (always-zero) design inside
  an `` `ifdef SYNTHESIS `` branch. See "Why the netlist gets re-simulated"
  below.

This is not a hypothetical: before the fixes below, both
`forged_pass_line.sv` and `ifdef_synthesis_differential.sv` actually fooled
the evaluator (see results table) — the latter scoring the maximum
possible reward of `2.0`.

### The fix for the forged pass line (defense in depth)

1. `policy.py` now rejects `$display`/`$write`/`$strobe`/`$monitor` and the
   severity tasks outright — a candidate can no longer write to stdout at
   all, forged or not.
2. `simulate.py` independently hardened: it used to take the *first* regex
   match of the mismatch-report line anywhere in stdout (`re.search`); it
   now requires **exactly one** match (`re.findall` + length check). Zero
   matches means the testbench never reached its own report (crash/timeout);
   more than one means something other than the testbench itself produced a
   line matching that pattern — never trusted.

Both defenses independently close the hole; keeping both means a future
change to one doesn't silently reopen it.

### Why the netlist gets re-simulated

The pipeline runs two separate tools over a candidate's source: Icarus
Verilog (stage 2, decides pass/fail) and Yosys (stage 3, decides the
reward via synthesis metrics). Before the fix, nothing forced these two
tools' views of the design to agree, and they don't always agree for
free: **Yosys's `read_verilog` defines the macro `SYNTHESIS` by default;
Icarus Verilog does not.** A candidate can exploit this directly:

```systemverilog
module TopModule(input [2:0] in, output [1:0] out);
`ifdef SYNTHESIS
  assign out = 2'b00;                     // what Yosys synthesizes: 0 cells
`else
  assign out = in[0] + in[1] + in[2];     // what Icarus simulates: correct
`endif
endmodule
```

Confirmed empirically: this passed simulation (220/220 samples, 0
mismatches — Icarus takes the `else` branch) and synthesized to
`assign out = 2'h0` (0 cells, 0 depth — Yosys takes the `` `ifdef ``
branch), for a reward of exactly `2.0`: the maximum the formula can
produce, and silently, since the formal check (which would catch this,
being exact for this purely combinational task) never gated the episode.

The fix closes the whole class, not just this one macro: stage 4
re-simulates the *actual netlist Yosys produced* (via `write_verilog`)
against the same trusted testbench, using Yosys's own `simcells.v` for
its internal gate primitives' behavior. Whatever synthesis produced is
what gets functionally checked, so there's no longer a design that's
"rewarded" without also being "verified." Running the exploit above
through `check_policy()` directly still catches it too — preprocessor
conditionals are now banned outright (see Pipeline above) — kept as a
cheaper first line of defense, same reasoning as the forged-pass-line
fix above: defense in depth, so narrowing one rule later doesn't silently
reopen the hole.

A related trick the same fix closes without any extra code: a candidate
writing to a hierarchical path outside its own module (e.g. `tb.errors`)
to tamper with the testbench's own bookkeeping directly — this doesn't
touch synthesis at all, but is independently banned by the same
hierarchical-reference policy rule added alongside the preprocessor ban.

### Why formal doesn't gate the episode

Yosys's SAT miter equivalence check (`miter -equiv` + `sat -prove-asserts
-verify`) is **exact for purely combinational designs**, but for sequential
designs the two circuits' internal register states are left free/
unconstrained relative to each other between the miter's input and output
ports — there is no temporal induction here, just a single-cycle
combinational comparison of the flattened miter. In practice this produces
false negatives: `pulse_shaping_fir`'s reference and a verified-correct
candidate both pass a 10,000+ cycle functional simulation against the
trusted testbench, but fail this miter check, because the check cannot
account for the two designs' pipeline/delay-line state being in different
(but behaviorally equivalent) phases. Gating on it would reject correct
sequential candidates, so it is recorded as a diagnostic
(`formal_equivalent` in `EvaluationResult`/`StepResult.info`) and never
fails the episode. See "Next steps" for a real fix (temporal induction).

## Results

Generated by `scripts/run_experiments.py`; raw data in
`runs/pass_at_k/results.json`.

### Pipeline sanity checks (not a pass@k estimate)

**This is deliberately not called pass@k.** pass@k (Chen et al., 2021)
names a specific estimator computed over many independent samples drawn
from a real model at some sampling temperature. What's below is a
handful of hand-written attempts per task, one of them wrong on purpose —
useful for checking that the pipeline actually distinguishes correct from
incorrect submissions, not for claiming anything about model capability.
A real pass@k study would sample 10–20 attempts per task from an actual
model across 20+ VerilogEval problems (including sequential ones) and
apply the unbiased estimator from that paper.

| task | attempts | fraction passed | any passed | per-attempt reward |
| --- | --- | --- | --- | --- |
| popcount3 | 3 | 0.67 | True | 1.00, 1.07, 0.00 |
| pulse_shaping_fir | 4 | 0.75 | True | 0.99, 1.01, 0.00, 0.96 |

Each task includes a deliberately plausible-but-wrong attempt (popcount3:
XOR/parity instead of a popcount; FIR: reversed tap order within each
phase), confirming the pipeline actually fails bad candidates rather than
passing everything. `pulse_shaping_fir`'s fourth attempt
(`attempt_4_spec_only.sv`) was written from the task's text prompt alone,
without looking at the reference or the other hand-written candidate, as
a (still informal) check that the spec itself is sufficient to implement
against.

### Reward hacking: before vs. after defenses

Reward recomputed for each adversarial example using the pre-fix
vulnerable pipeline (no policy gate beyond `$system`/file-I/O/`` `include``/
`$finish`/`$stop`, `simulate.py`'s old `re.search`, and no netlist
re-simulation) versus the current defended pipeline:

| adversarial file | reward before | reward after | stage (after) |
| --- | --- | --- | --- |
| forged_pass_line.sv | 1.90 | 0.00 | policy |
| ifdef_synthesis_differential.sv | 2.00 | 0.00 | policy |
| system_call.sv | 0.00 | 0.00 | policy |

`forged_pass_line.sv` and `ifdef_synthesis_differential.sv` are the two
confirmed exploits. The latter is the more serious of the two: it scored
the maximum possible reward (`2.0`) completely silently — a functional
pass plus a *maximal* synthesis bonus, since the netlist Yosys actually
saw was reduced to a single constant assignment. `system_call.sv` was
already rejected before this round of fixes (an earlier `$system` policy
rule already existed); it's included as a regression check.

### An unrelated bug found while producing these results

While investigating why `pulse_shaping_fir`'s otherwise-correct attempts
scored `reward: 0.0` despite passing simulation, `synthesize.py` turned out
to have a metrics-extraction bug independent of the reward-hacking work:
Yosys's `stat` reports per-module statistics for hierarchical designs
(a top module that instantiates submodules only counts one "cell" per
submodule instance, not that submodule's internal cells), and `synth`
itself prints its own internal pre-flatten stat report earlier in stdout
than our explicit `stat` call, so a plain `re.search` picked up that
stale, drastically undercounted first match. Fixed by flattening before
`stat`/`ltp` and taking the *last* regex match of each metric instead of
the first. This is why the table above shows sane rewards (0.99/1.01)
for `pulse_shaping_fir`'s correct attempts instead of the `0.0` the bug
originally produced.

## Reward is relative to the reference

The reward formula measures the candidate's cell count and logic depth
*against the reference's*, not against any absolute notion of "small" or
"fast." This is deliberate — it's the only way to get a reward near `1.0`
for a reasonable implementation without hand-picking per-task thresholds —
but it means **the reward is only as good as the reference**. If the
reference implementation itself is unnecessarily large or deep (an
inefficient coding style, a missed optimization, extra pipeline stages
that weren't needed), every candidate is graded against that inflated
bar, and a candidate that's merely *competent* can look like it's scoring
below `1.0` ("worse than reference") when it's actually just as good an
implementation as a human would write — the reference was simply loose.
Conversely, an unusually tight, hand-optimized reference sets a bar that
even a correct, idiomatic candidate may not clear. This isn't fixed by
anything in the current pipeline; it would need either a reference
written specifically to be a tight baseline (not just "a working
implementation," which is all VerilogEval's references are), or an
absolute metric independent of any one reference (e.g. a published
PPA budget for the task), neither of which this project currently has.

## A note on policy enforcement

`policy.py` is a set of regexes, not a parser, and that's a real
limitation beyond what's fixed above: a regex like `\$display\w*\b`
matches known spellings, but can't reason about what a candidate
constructs out of macros, nor does it understand Verilog's actual
grammar (comments, string literals, and generate-block text could all,
in principle, confuse a regex that a real parser wouldn't be fooled by).
The stronger design — tracked, not yet built — is to parse the candidate
with a real front end (e.g. `pyslang`, or Verilator's lint output) and
check its AST against an explicit allowlist of permitted constructs,
rather than a denylist of regexes. The exactly-once mismatch-report check
in `simulate.py` and the netlist re-simulation gate in `evaluator.py` are
both independent of `policy.py` and don't share this weakness, which is
why both of those exist rather than relying on policy alone.

## Next steps

- **Sequential equivalence checking.** Replace (or augment) the single-cycle
  SAT miter with Yosys's `equiv_induct`/temporal induction (or a bounded
  model-checking pass over several cycles) so formal checking can actually
  gate sequential designs like `pulse_shaping_fir` instead of being
  diagnostic-only.
- **A real pass@k study.** Sample 10–20 attempts per task from an actual
  model across 20+ VerilogEval problems (including sequential ones) and
  report the Chen et al. (2021) unbiased estimator, instead of the hand-
  written sanity checks this currently has.
- **Parser-based policy enforcement.** Replace (or back up) the regex
  denylist with an AST-based allowlist (see "A note on policy enforcement"
  above).
- **Multi-step episodes.** Currently `RTLRewardEnv.step()` is a single shot:
  submit once, get a scalar reward. A more realistic RL framing would let
  the policy see evaluator feedback (which stage failed, which policy rule,
  which mismatch count) and resubmit within the same episode, closer to how
  an LLM-driven agent would actually iterate.
- **Slow EDA tools.** Yosys/Icarus runs here are fast because the tasks are
  small. Larger designs make `synth`/`sat` run for minutes; the runner's
  timeout and resource limits exist but a real pipeline would need async/
  job-queue execution rather than blocking `step()` calls, plus caching of
  synthesis results across repeated evaluations of the same candidate.
