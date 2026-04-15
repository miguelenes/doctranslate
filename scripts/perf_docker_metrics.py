#!/usr/bin/env python3
"""Record Docker image size and cold ``docker run`` startup for CPU/API targets."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


def _run(
    cmd: list[str], *, timeout: float | None = 600
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _image_size_bytes(image_ref: str) -> int | None:
    proc = _run(
        [
            "docker",
            "image",
            "inspect",
            image_ref,
            "--format",
            "{{.Size}}",
        ],
        timeout=60,
    )
    if proc.returncode != 0:
        return None
    text = (proc.stdout or "").strip()
    try:
        return int(text)
    except ValueError:
        return None


def _time_run(image_ref: str, extra_args: list[str]) -> tuple[int, float, str]:
    """``docker run --rm`` … ``IMAGE`` followed by optional command args."""
    t0 = time.perf_counter()
    proc = _run(
        ["docker", "run", "--rm", *extra_args, image_ref],
        timeout=300,
    )
    elapsed = time.perf_counter() - t0
    tail = ((proc.stderr or "") + (proc.stdout or ""))[-4000:]
    return proc.returncode, elapsed, tail


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cpu-tag",
        default="doctranslater:perf-cpu",
        help="Local tag for runtime-cpu image",
    )
    parser.add_argument(
        "--api-tag",
        default="doctranslater:perf-api",
        help="Local tag for runtime-api image",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Assume images already exist locally",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent

    if not args.skip_build:
        for target, tag in (
            ("runtime-cpu", args.cpu_tag),
            ("runtime-api", args.api_tag),
        ):
            proc = _run(
                [
                    "docker",
                    "build",
                    "--target",
                    target,
                    "-t",
                    tag,
                    str(root),
                ],
                timeout=3600,
            )
            if proc.returncode != 0:
                sys.stderr.write(proc.stderr or proc.stdout or "docker build failed\n")
                return proc.returncode or 1

    report: dict[str, object] = {"schema_version": 1, "images": {}}

    for name, tag in (("runtime_cpu", args.cpu_tag), ("runtime_api", args.api_tag)):
        size = _image_size_bytes(tag)
        code2, elapsed2, tail2 = _time_run(
            tag,
            ["--entrypoint", "", "doctranslate", "--version"],
        )
        report["images"][name] = {
            "tag": tag,
            "size_bytes": size,
            "doctranslate_version_exit": code2,
            "doctranslate_version_seconds": round(elapsed2, 4),
            "version_log_tail": tail2,
        }

    # API HTTP readiness (auth disabled in bench): hit /health from inside the container.
    api_tag = args.api_tag
    _run(["docker", "rm", "-f", "doctranslater-perf-api"], timeout=30)
    proc = _run(
        [
            "docker",
            "run",
            "-d",
            "--rm",
            "-p",
            "18080:8000",
            "-e",
            "DOCTRANSLATE_API_AUTH_MODE=disabled",
            "-e",
            "DOCTRANSLATE_API_DATA_ROOT=/tmp/perf-api-data",
            "--name",
            "doctranslater-perf-api",
            api_tag,
        ],
        timeout=120,
    )
    health: dict[str, object] = {
        "docker_run_detach_exit": proc.returncode,
        "http_health_seconds": None,
        "http_health_status": None,
    }
    if proc.returncode == 0:
        t0 = time.perf_counter()
        for _ in range(60):
            h = _run(
                [
                    "docker",
                    "exec",
                    "doctranslater-perf-api",
                    "python",
                    "-c",
                    "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).read()",
                ],
                timeout=30,
            )
            if h.returncode == 0:
                health["http_health_seconds"] = round(time.perf_counter() - t0, 4)
                health["http_health_status"] = "ok"
                break
            time.sleep(1)
        else:
            health["http_health_status"] = "timeout"
        _run(["docker", "stop", "doctranslater-perf-api"], timeout=60)
    else:
        health["stderr"] = (proc.stderr or "")[-2000:]

    report["api_container_health"] = health

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
