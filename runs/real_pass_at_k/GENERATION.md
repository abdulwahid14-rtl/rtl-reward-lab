# How the 200 real-pass@k samples were generated

This documents exactly how `runs/real_pass_at_k/samples/` was produced, so
the pass@1 numbers in `docs/reward-design.md` can actually be interpreted
rather than taken on faith.

## Model

**Claude Sonnet 5** (model id `claude-sonnet-5`) — the same model this
Claude Code session itself runs on. Generated 2026-10-23.

This is a real, if narrow, limitation of the setup: there was no access
to a second model or to the raw Anthropic API from inside this session,
so "a real pass@k study" here means "real independent samples from
Claude," not "samples from an arbitrary model of the author's choosing."
A wider study comparing multiple models would need to run outside this
tool.

## How each sample was produced

Each of the 200 samples came from its own call to Claude Code's `Agent`
tool, `subagent_type: "general-purpose"`, with no `model` override (so it
ran on this session's own default model). Each such call starts a
**fresh agent instance with no memory of this conversation or of any
other sample** — it does not inherit this session's context, does not
see the task's reference implementation or testbench, and cannot see any
other sample for the same or a different task. 10 samples per task × 20
tasks were generated in 10 "rounds" (one round = 20 parallel calls, one
per task), round-robin across tasks, not 20 sequential calls per task.

The exact prompt template given to every sample (task prompt text
substituted in, otherwise byte-identical across all 200 calls):

```
You are implementing a single Verilog module from a spec, for a
code-generation benchmark. Respond with ONLY the complete
SystemVerilog/Verilog source code for the module -- no explanation
before or after. Do NOT use any tools (no Bash, no file read/write, no
self-testing). This must be a single-shot response based purely on
reading the spec below, like a one-shot code-completion model, not an
iteratively-debugged one.

Spec:

<task's prompt.txt verbatim>

Respond with just the Verilog code for `module TopModule ... endmodule`.
```

(`Prob031_dff` additionally got one sentence noting the prompt's own
apparent `input q` port-direction typo and asking the model to use its
own judgment — this is a known quirk of the upstream VerilogEval prompt
text itself, not something introduced for this study.)

Each call ran as a general-purpose coding agent, which has tool access by
default; it was explicitly instructed not to use any tools, and in
practice none of the 200 transcripts show a tool call (consistent with
`tool_uses: 0` reported for every sample) -- but this is an instruction
followed, not a hard constraint the harness enforces, which is weaker
than a true API completion call with tools disabled entirely.

## Sampling settings

**Not controllable from this interface.** The `Agent` tool does not
expose temperature, top-p, or any other sampling parameter -- it runs
whatever default decoding settings the harness uses for a
`general-purpose` subagent. This means the 10 samples per task are
independent draws, but not characterized draws: there's no stated
temperature to report, and no guarantee the effective sampling
temperature matches what "pass@k" conventionally assumes (Chen et al.,
2021 samples at a fixed, stated temperature, usually tuned per-k). The
unbiased pass@k estimator itself doesn't require knowing the
temperature, so the numbers are still a legitimate pass@1 over 10 real
independent samples -- but reproducing this exact study, or comparing it
to a pass@k number from a different setup, would need a direct API-based
generation script instead of this tool-based approach.

## How independence was kept

- Each sample is a separate `Agent` call with `subagent_type:
  "general-purpose"` (never `"fork"`, which would inherit this
  conversation's context). Fresh agents share no memory, prompt cache
  content, or state with each other or with this conversation.
- No sample's prompt mentions or includes any other sample, the
  reference implementation, or the trusted testbench -- only the task's
  own `prompt.txt` text.
- Generation order was round-robin (round 1 = sample 1 of all 20 tasks,
  ..., round 10 = sample 10 of all 20 tasks), not all 10 samples for one
  task back-to-back, so there's no structural reason for within-task
  samples to be more similar to each other than to samples from other
  rounds.

## A more reproducible version of this study

The cleanest fix for the two limitations above (uncharacterized
sampling, and "whichever model Claude Code defaults to" rather than a
deliberately chosen one) is to replace the `Agent`-tool generation step
with a short, direct script against the Anthropic Messages API (or
another provider's), explicitly passing `model` and `temperature` and
logging both alongside the raw completions. The evaluation side
(`scripts/run_real_pass_at_k.py`) doesn't change either way -- it just
reads whatever is in `runs/real_pass_at_k/samples/`.
