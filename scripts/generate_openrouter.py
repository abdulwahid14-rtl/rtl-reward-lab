"""Generate pulse_shaping_fir candidates from other providers via OpenRouter.

    export OPENROUTER_API_KEY=...      # read from the environment only
    python3 scripts/generate_openrouter.py --models openai/gpt-5 google/gemini-2.5-pro

Uses the same prompt wrapper as the Claude samples in runs/pulse_fir_models/
(the task's prompt.txt, no reference, no testbench, no tools). One request per
sample, default sampling (no temperature/top_p sent), standard library only.

Writes, per model, under --out (default runs/pulse_fir_models/):
  <provider>_<model>/sample_NN.sv
  <provider>_<model>/generation_log.jsonl   served model, request id, finish
                                            reason, token usage, prompt hash,
                                            raw response text

Re-running resumes: samples already on disk are skipped. The API key is never
written to disk or logged. Use --dry-run to print the first request without
sending anything.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from rtl_reward_lab.passk import REPO_ROOT, extract_verilog

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_TASK_DIR = REPO_ROOT / "examples" / "correct" / "pulse_shaping_fir"

# Identical wording to the wrapper given to the Haiku/Sonnet/Opus sub-agents.
WRAPPER_HEAD = (
    "You are implementing a single Verilog module from a spec, for a code-generation "
    "benchmark. Respond with ONLY the complete SystemVerilog/Verilog source code for the "
    "module -- no explanation before or after. Do NOT use any tools (no Bash, no file "
    "read/write, no self-testing). This must be a single-shot response based purely on "
    "reading the spec below.\n\nSpec:\n\n"
)
WRAPPER_TAIL = "\n\nRespond with just the Verilog code for `module TopModule ... endmodule`."


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def build_prompt(task_dir: Path) -> str:
    return WRAPPER_HEAD + (task_dir / "prompt.txt").read_text().rstrip() + WRAPPER_TAIL


def _post(payload: dict, key: str, retries: int = 4) -> dict:
    body = json.dumps(payload).encode()
    for attempt in range(retries + 1):
        request = urllib.request.Request(
            ENDPOINT,
            data=body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            retryable = exc.code == 429 or exc.code >= 500
            if not retryable or attempt == retries:
                raise SystemExit(f"{payload['model']}: HTTP {exc.code}: {exc.read().decode()[:300]}")
        except urllib.error.URLError as exc:
            if attempt == retries:
                raise SystemExit(f"{payload['model']}: {exc.reason}")
        time.sleep(2 ** attempt * 2)
    raise AssertionError("unreachable")


def _generate_one(model: str, idx: int, prompt: str, args, key: str) -> None:
    model_dir = args.out / model.replace("/", "_")
    sample_path = model_dir / f"sample_{idx:02d}.sv"
    if sample_path.exists():
        return

    reply = _post(
        {"model": model, "max_tokens": args.max_tokens, "messages": [{"role": "user", "content": prompt}]},
        key,
    )
    choice = reply["choices"][0]
    raw_text = choice["message"].get("content") or ""
    record = {
        "model_requested": model,
        "sample": idx,
        "model_served": reply.get("model"),
        "request_id": reply.get("id"),
        "finish_reason": choice.get("finish_reason"),
        "usage": reply.get("usage"),
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "finished_at": _now(),
        "raw_text": raw_text,
    }
    model_dir.mkdir(parents=True, exist_ok=True)
    # Log before writing the sample so a sample on disk always has its log line.
    with (model_dir / "generation_log.jsonl").open("a") as log:
        log.write(json.dumps(record) + "\n")
    sample_path.write_text(extract_verilog(raw_text))
    print(f"{model} sample {idx:02d}: {choice.get('finish_reason')}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--models", nargs="+", required=True, help="OpenRouter model ids, e.g. openai/gpt-5")
    parser.add_argument("--n", type=int, default=1, help="samples per model")
    parser.add_argument("--max-tokens", type=int, default=16000)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--task-dir", type=Path, default=DEFAULT_TASK_DIR)
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "runs" / "pulse_fir_models")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    prompt = build_prompt(args.task_dir)
    if args.dry_run:
        print(f"POST {ENDPOINT}\nmodels: {args.models}  n={args.n}  max_tokens={args.max_tokens}\n---\n{prompt}")
        return

    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY is not set in the environment")

    jobs = [(m, i) for i in range(1, args.n + 1) for m in args.models]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for future in [pool.submit(_generate_one, m, i, prompt, args, key) for m, i in jobs]:
            future.result()


if __name__ == "__main__":
    main()
