#!/usr/bin/env python3
"""Manual benchmark helper for local translation (requires a running local LLM)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True, help="Input PDF path")
    parser.add_argument("--lang-in", default="en")
    parser.add_argument("--lang-out", default="zh")
    parser.add_argument(
        "--backend",
        choices=["ollama", "vllm", "llama-cpp", "openai-compatible"],
        default="ollama",
    )
    parser.add_argument("--model", required=True, help="Model id for --local-model")
    parser.add_argument("--base-url", default=None, help="Optional --local-base-url")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory")
    args = parser.parse_args()

    if not args.pdf.exists():
        print(f"PDF not found: {args.pdf}", file=sys.stderr)
        return 2

    out = args.out_dir or Path(tempfile.mkdtemp(prefix="doctranslate_bench_"))
    if args.out_dir is not None:
        out.mkdir(parents=True, exist_ok=True)

    # ``python -m doctranslate.main`` matches the package entrypoint behavior.
    cmd = [
        sys.executable,
        "-m",
        "doctranslate.main",
        "--translator",
        "local",
        "--local-backend",
        args.backend,
        "--local-model",
        args.model,
        "--files",
        str(args.pdf),
        "--lang-in",
        args.lang_in,
        "--lang-out",
        args.lang_out,
        "--output",
        str(out),
    ]
    if args.base_url:
        cmd.extend(["--local-base-url", args.base_url])

    t0 = time.perf_counter()
    proc = subprocess.run(cmd, check=False)  # noqa: S603
    elapsed = time.perf_counter() - t0

    report = {
        "exit_code": proc.returncode,
        "elapsed_seconds": round(elapsed, 3),
        "command": cmd,
    }
    print(json.dumps(report, indent=2))
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
