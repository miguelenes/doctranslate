"""CLI JSON envelope and translate flag contract tests."""

from __future__ import annotations

import json

from doctranslate.cli.dispatch import build_vnext_parser
from doctranslate.cli.output import OutputContext


def test_output_context_json_includes_schema_version() -> None:
    ctx = OutputContext(format="json", command="test")
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        ctx.emit_result(True, {"x": 1})
    data = json.loads(buf.getvalue().strip())
    assert data["ok"] is True
    assert data["schema_version"] == "1"
    assert data["stream"] == "final"
    assert data["result"]["x"] == 1


def test_translate_parser_has_request_json_flags() -> None:
    p = build_vnext_parser()
    args = p.parse_args(
        [
            "translate",
            "--request-json",
            "req.json",
            "--emit-progress-json",
            "a.pdf",
            "--translator",
            "openai",
        ],
    )
    assert args.request_json == "req.json"
    assert args.emit_progress_json is True


def test_translate_output_format_after_subcommand() -> None:
    p = build_vnext_parser()
    args = p.parse_args(
        [
            "translate",
            "a.pdf",
            "--translator",
            "openai",
            "--output-format",
            "json",
        ],
    )
    assert args.translate_output_format == "json"
