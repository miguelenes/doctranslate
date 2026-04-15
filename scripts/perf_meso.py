#!/usr/bin/env python3
"""Meso-benchmarks: subprocess CLI timings (JSON to stdout).

Measures ``--help``, ``inspect``, ``assets warmup``, and ``translate`` with
``--skip-translation`` (no LLM traffic; dummy ``OPENAI_API_KEY`` only to satisfy CLI).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def _time_cmd(
    cmd: list[str],
    *,
    env: dict[str, str] | None = None,
) -> tuple[int, float]:
    t0 = time.perf_counter()
    proc = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    elapsed = time.perf_counter() - t0
    return proc.returncode, elapsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pdf",
        type=Path,
        default=None,
        help="Sample PDF (default: repo examples/ci/test.pdf)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (default: parent of scripts/)",
    )
    args = parser.parse_args()
    repo = (args.repo_root or Path(__file__).resolve().parent.parent).resolve()
    pdf = args.pdf or (repo / "examples" / "ci" / "test.pdf")
    if not pdf.is_file():
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "error": "missing_pdf",
                    "path": str(pdf),
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2

    base_env = os.environ.copy()
    translate_env = base_env.copy()
    translate_env.setdefault("OPENAI_API_KEY", "sk-perf-benchmark-not-called")

    out_dir = repo / ".benchmarks" / "meso_out"
    out_dir.mkdir(parents=True, exist_ok=True)

    exe = sys.executable
    mod = [exe, "-m", "doctranslate.main"]

    rows: list[dict[str, object]] = []

    def add_row(name: str, code: int, seconds: float, extra: dict | None = None):
        row: dict[str, object] = {
            "name": name,
            "exit_code": code,
            "elapsed_seconds": round(seconds, 4),
        }
        if extra:
            row.update(extra)
        rows.append(row)

    c1, t1 = _time_cmd([*mod, "--help"], env=base_env)
    add_row("cli_help", c1, t1)

    c2, t2 = _time_cmd(
        [*mod, "--output-format", "json", "inspect", str(pdf)],
        env=base_env,
    )
    add_row("cli_inspect_json", c2, t2)

    c3, t3 = _time_cmd([*mod, "assets", "warmup"], env=base_env)
    add_row("cli_assets_warmup", c3, t3)

    translate_cmd = [
        *mod,
        "translate",
        str(pdf),
        "--provider",
        "openai",
        "--openai-api-key",
        translate_env["OPENAI_API_KEY"],
        "--skip-translation",
        "--skip-scanned-detection",
        "--no-auto-extract-glossary",
        "--lang-in",
        "en",
        "--lang-out",
        "zh",
        "-o",
        str(out_dir),
    ]
    c4, t4 = _time_cmd(translate_cmd, env=translate_env)
    add_row("cli_translate_skip_translation", c4, t4)

    report = {
        "schema_version": 1,
        "repo_root": str(repo),
        "pdf": str(pdf),
        "steps": rows,
    }
    print(json.dumps(report, indent=2))
    worst = max((r["exit_code"] for r in rows), default=0)
    return int(worst) if worst else 0


if __name__ == "__main__":
    raise SystemExit(main())
