# pulse_shaping_fir: single-shot samples from three models

Nine samples written from `examples/correct/pulse_shaping_fir/prompt.txt`
alone, scored with the full pipeline against `reference.sv` (3063 cells,
logic depth 31).

## How they were generated

Each sample is one Claude Code sub-agent call with a model override
(`haiku`, `sonnet`, `opus`), on 2026-10-27. The agent saw only the prompt
text inside the same wrapper used for `runs/real_pass_at_k/` ("respond with
only the code, no tools"). It saw no reference, testbench or other sample.
Sampling settings and request IDs are not logged (see
`runs/real_pass_at_k/GENERATION.md` for why).

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

`haiku/sample_03.sv` is kept as generated: it ends the module with `}`
instead of `endmodule` and drives `OwSampleOut_2` from `acc[1]`.

Eight of nine pass, and none is smaller than the reference. All eight
passing samples use a generic `tap * coeff` multiply, so none uses the
prompt's ternary-input restriction. Nine samples cannot rank the models:
the two Opus runs differ from each other by more than the gap between
Haiku and Sonnet.
