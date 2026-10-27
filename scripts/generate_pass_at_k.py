"""Generate pass@k samples by calling the Anthropic API directly.

Reproducible counterpart to the Claude Code sub-agent run in
runs/real_pass_at_k/: same 20 tasks and the same prompt (rtl_reward_lab.passk),
but every request's settings and the raw response are logged, so anyone with
an API key can rerun it and get a comparable study.

    pip install -e '.[generate]'
    export ANTHROPIC_API_KEY=...      # or `ant auth login`
    python3 scripts/generate_pass_at_k.py --model claude-opus-5-5
    python3 scripts/run_real_pass_at_k.py --run-dir runs/pass_at_k_api/claude-opus-5-5

Writes, under --out (default runs/pass_at_k_api/<model>/):
  run_config.json         settings shared by every request
  generation_log.jsonl    one line per sample: response model, request id,
                          stop reason, token usage, prompt hash, raw text
  samples/<task>/sample_NN.sv

Re-running resumes: samples already on disk are skipped.

Sampling: no temperature/top_p/top_k are sent. Current Claude models accept
only the API's default sampling, so there is no knob to set; the run config
records that rather than a number nobody chose.

Refusal fallbacks are deliberately not enabled. A server-side fallback would
re-run a declined request on a different model, mixing models inside one
pass@k study. A refusal or max_tokens stop is logged and its (possibly empty)
output kept as the sample, so it counts as a failure rather than being
silently dropped.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    import anthropic
except ImportError as exc:  # pragma: no cover - environment check
    raise SystemExit("anthropic SDK not installed: pip install -e '.[generate]'") from exc

from rtl_reward_lab.passk import REPO_ROOT, TASK_IDS, build_prompt, extract_verilog, task


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _generate_one(client, args, task_id: str, sample_idx: int, out_dir: Path, log_path: Path, lock):
    sample_path = out_dir / "samples" / task_id / f"sample_{sample_idx:02d}.sv"
    if sample_path.exists():
        return

    prompt = build_prompt(task_id, task(task_id).prompt_path.read_text())
    with client.messages.stream(
        model=args.model,
        max_tokens=args.max_tokens,
        output_config={"effort": args.effort},
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        message = stream.get_final_message()

    raw_text = "".join(block.text for block in message.content if block.type == "text")
    record = {
        "task_id": task_id,
        "sample": sample_idx,
        "requested_model": args.model,
        "response_model": message.model,
        "request_id": message._request_id,
        "stop_reason": message.stop_reason,
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "finished_at": _now(),
        "raw_text": raw_text,
    }
    # Log before writing the sample: resume skips on the sample file, so a
    # sample on disk always has its log line.
    with lock, log_path.open("a") as log:
        log.write(json.dumps(record) + "\n")
    sample_path.parent.mkdir(parents=True, exist_ok=True)
    sample_path.write_text(extract_verilog(raw_text))
    print(f"{task_id} sample {sample_idx:02d}: {message.stop_reason}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", default="claude-opus-5-5")
    parser.add_argument("--n", type=int, default=10, help="samples per task")
    parser.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--max-tokens", type=int, default=32000)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--tasks", nargs="*", default=TASK_IDS)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    out_dir = args.out or REPO_ROOT / "runs" / "pass_at_k_api" / args.model
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "generation_log.jsonl"

    config_path = out_dir / "run_config.json"
    if not config_path.exists():
        config_path.write_text(json.dumps({
            "model": args.model,
            "n_per_task": args.n,
            "tasks": args.tasks,
            "effort": args.effort,
            "max_tokens": args.max_tokens,
            "thinking": "not sent (model default: adaptive)",
            "sampling": "no temperature/top_p/top_k sent; API default sampling (the only setting current models accept)",
            "fallbacks": "disabled, so every sample comes from the requested model",
            "tools": "none",
            "anthropic_sdk_version": anthropic.__version__,
            "started_at": _now(),
        }, indent=2))

    client = anthropic.Anthropic(max_retries=5)
    lock = threading.Lock()
    # Round-robin order (sample 1 of every task, then sample 2, ...), as in the
    # sub-agent run, so no task's samples are generated back-to-back.
    jobs = [(t, i) for i in range(1, args.n + 1) for t in args.tasks]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(_generate_one, client, args, t, i, out_dir, log_path, lock) for t, i in jobs]
        for future in futures:
            future.result()


if __name__ == "__main__":
    main()
