"""Human and JSON CLI output helpers."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any


@dataclass
class OutputContext:
    """Per-invocation output mode."""

    format: str = "human"  # human | json
    command: str = ""

    def is_json(self) -> bool:
        return self.format == "json"

    def emit_result(
        self, ok: bool, result: Any | None = None, warnings: list | None = None
    ) -> None:
        if not self.is_json():
            return
        envelope: dict[str, Any] = {
            "ok": ok,
            "command": self.command,
            "result": result,
            "warnings": warnings or [],
            "errors": [],
        }
        sys.stdout.write(json.dumps(envelope, ensure_ascii=False) + "\n")

    def emit_error(
        self,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        if self.is_json():
            sys.stdout.write(
                json.dumps(
                    {
                        "ok": False,
                        "command": self.command,
                        "result": None,
                        "warnings": [],
                        "errors": [],
                        "error": {
                            "code": code,
                            "message": message,
                            "details": details or {},
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n",
            )
        else:
            sys.stderr.write(f"{code}: {message}\n")
