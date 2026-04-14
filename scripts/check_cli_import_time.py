#!/usr/bin/env python3
"""Log import and parser-build times for CI (warn-only; always exits 0)."""

from __future__ import annotations

import json
import logging
import time

log = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    t0 = time.perf_counter()
    import doctranslate.cli.dispatch as dispatch  # noqa: PLC0415

    t1 = time.perf_counter()
    dispatch.build_vnext_parser()
    t2 = time.perf_counter()
    data = {
        "import_dispatch_s": round(t1 - t0, 3),
        "build_parser_s": round(t2 - t1, 3),
        "total_s": round(t2 - t0, 3),
    }
    log.info("cli_import_profile %s", json.dumps(data))
    # Optional threshold (seconds): log warning only; never fail CI on this step.
    warn_if_above = 8.0
    if data["total_s"] > warn_if_above:
        log.warning(
            "cli_import_profile exceeds soft threshold: total_s=%s (warn_if_above=%s)",
            data["total_s"],
            warn_if_above,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
