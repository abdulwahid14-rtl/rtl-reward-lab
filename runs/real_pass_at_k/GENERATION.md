# How the 200 real-pass@k samples were generated

This documents exactly how I produced `runs/real_pass_at_k/samples/`, so
the pass@1 numbers in `docs/reward-design.md` can actually be
interpreted rather than taken on faith.

## Model

I generated the samples with **Claude Sonnet 5** (model id
`claude-sonnet-5`), via Claude Code sub-agents, on 2026-10-23.

This is a real, if narrow, limitation of the setup: I didn't have access
to a second model or to the raw Anthropic API from inside the Claude
Code session I was using, so "a real pass@k study" here means real
independent samples from Claude, not samples from a model I chose
specifically for this purpose. A wider study comparing multiple models
would need a separate, direct API-based generation script (see "A more
reproducible version of this study" below).

## How each sample was produced

Each of the 200 samples came from its own call to Claude Code's `Agent`
tool (`subagent_type: "general-purpose"`), with no model override, so
each ran on Claude Sonnet 5. Each such call starts a **fresh agent
instance with no memory of my conversation with Claude Code or of any
other sample** — it doesn't see that conversation's context, doesn't see
the task's reference implementation or testbench, and can't see any
other sample for the same or a different task. I generated 10 samples
per task × 20 tasks in 10 "rounds" (one round = 20 parallel calls, one
per task), round-robin across tasks rather than 20 sequential calls for
one task at a time.

The prompt template I used (task prompt text substituted in). 199 of the
200 calls used exactly this wording; the very first one (`Prob003_step_one`
sample 1) used an earlier draft whose first sentence also said "no
markdown fences needed (but fine if you include them)". Each sub-agent
also runs under Claude Code's own system prompt, which I don't control:

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
own judgment — a known quirk of the upstream VerilogEval prompt text
itself, not something I introduced for this study.)

Each sample ran as a general-purpose coding agent, which has tool access
by default; I explicitly instructed it not to use any tools, and in
practice none of the 200 transcripts show a tool call (consistent with
`tool_uses: 0` reported for every sample) — but that's an instruction
followed, not a hard constraint the harness enforces, which is weaker
than a true API completion call with tools disabled entirely.

## Sampling settings

**Not controllable from this interface.** Claude Code's `Agent` tool
doesn't expose temperature, top-p, or any other sampling parameter — it
runs whatever default decoding settings the harness uses for a
`general-purpose` sub-agent. So the 10 samples per task are independent
draws, but not characterized ones: I can't state a temperature, and I
have no guarantee the effective sampling temperature matches what
"pass@k" conventionally assumes (Chen et al., 2021 sample at a fixed,
stated temperature, usually tuned per-k). The unbiased pass@k estimator
itself doesn't require knowing the temperature, so the numbers are still
a legitimate pass@1 over 10 real independent samples — but reproducing
this exact study, or comparing it to a pass@k number from a different
setup, would need a direct API-based generation script instead of this
tool-based approach.

One correction to how I first framed this: even through the API, current
Claude models no longer accept `temperature`, `top_p` or `top_k` at all —
only the API's default sampling. So the gap isn't "I couldn't log the
temperature I used"; it's that nobody can choose one for these models.
What the sub-agent route actually loses is the log: which exact model
served each sample, its request ID, stop reason, and token usage.

## How I kept the samples independent

- Each sample is a separate `Agent` call with `subagent_type:
  "general-purpose"` (never `"fork"`, which would inherit the calling
  conversation's context). Fresh agents share no memory, prompt cache
  content, or state with each other.
- No sample's prompt mentions or includes any other sample, the
  reference implementation, or the trusted testbench — only the task's
  own `prompt.txt` text.
- I generated them round-robin (round 1 = sample 1 of all 20 tasks, ...,
  round 10 = sample 10 of all 20 tasks), not all 10 samples for one task
  back-to-back, so there's no structural reason for within-task samples
  to be more similar to each other than to samples from other rounds.

## A reproducible version of this study

`scripts/generate_pass_at_k.py` replaces the sub-agent step with direct
Anthropic API calls. It uses the same 20 tasks and the same prompt
template (both live in `rtl_reward_lab.passk`, shared with the evaluator),
sent as the only message with no system prompt,
lets me pick the model explicitly, and logs everything the sub-agent run
couldn't: a `run_config.json` with the shared settings (model, effort,
`max_tokens`, no tools, no sampling parameters, refusal fallbacks
disabled so no sample is served by a different model), and one
`generation_log.jsonl` line per sample with the model that actually
served it, the request ID, stop reason, token usage, a hash of the
prompt, and the raw response text.

```bash
pip install -e '.[generate]'
python3 scripts/generate_pass_at_k.py --model claude-opus-5-5
python3 scripts/run_real_pass_at_k.py --run-dir runs/pass_at_k_api/claude-opus-5-5
```

Passing `--model claude-sonnet-5` reruns this study's model through the
logged path, which shows how much the sub-agent harness itself moved the
numbers.
