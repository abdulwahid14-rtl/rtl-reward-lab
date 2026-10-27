# pulse_shaping_fir: single-shot samples from several models

Thirteen samples written from `examples/correct/pulse_shaping_fir/prompt.txt`
alone, scored with the full pipeline against `reference.sv` (3063 cells,
logic depth 31).

## How they were generated

- **Claude (`haiku/`, `sonnet/`, `opus/`):** one Claude Code sub-agent call per
  sample with a model override, on 2026-10-27. Sampling settings and request
  IDs are not logged (see `runs/real_pass_at_k/GENERATION.md` for why).
- **OpenAI GPT-6 (`openai_*/`):** `scripts/generate_openrouter.py` through
  OpenRouter, one request per sample, default sampling. Each directory has a
  `generation_log.jsonl` with the served model, request id, finish reason,
  token usage and raw response.

Both routes use the same prompt wrapper ("respond with only the code, no
tools") around the prompt text. No sample saw the reference, the testbench or
any other sample.

Two `fable` samples were attempted and failed before producing code (the
account needs usage credits for that model), so there are no Fable results.
An earlier hand-written candidate was dropped: it was written with the
reference in view, so it was not a fair comparison.

## Results

| model | sample | passes | cells | depth | vs. reference cells |
| --- | --- | --- | --- | --- | --- |
| haiku | 01 | yes | 4091 | 38 | +34% |
| haiku | 02 | yes | 3610 | 38 | +18% |
| haiku | 03 | no  | - | - | - |
| sonnet | 01 | yes | 3625 | 38 | +18% |
| sonnet | 02 | yes | 3715 | 41 | +21% |
| sonnet | 03 | yes | 3609 | 38 | +18% |
| opus | 01 | yes | 3990 | 44 | +30% |
| opus | 02 | yes | 3673 | 41 | +20% |
| opus | 03 | yes | 3676 | 41 | +20% |
| gpt-6-luna | 01 | yes | 3768 | 54 | +23% |
| gpt-6.1-terra | 01 | yes | 3558 | 37 | +16% |
| gpt-6.1-sol | 01 | yes | 3866 | 54 | +26% |
| gpt-6-astra | 01 | yes | 3866 | 54 | +26% |

`haiku/sample_03.sv` is kept as generated: it ends the module with `}`
instead of `endmodule` and drives `OwSampleOut_2` from `acc[1]`.

Twelve of thirteen pass, and none is smaller or shallower than the
reference. Eleven of the twelve passing samples use a generic `tap * coeff`
multiply. The exception is `gpt-6.1-terra`, which selects `+coeff`, `-coeff`
or `0` from the sample bits, so it is the only one that uses the prompt's
ternary-input restriction (and the smallest and shallowest of the passing
samples). `gpt-6-astra` and `gpt-6.1-sol` produced the same cell count and
depth and differ only in naming and formatting. With one to three samples per
model, this cannot rank the models.
