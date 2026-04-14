"""CLI parser smoke tests for translator flags."""

from pathlib import Path

from doctranslate.main import create_parser


def test_parser_accepts_translator_router_flags(tmp_path: Path):
    cfg = tmp_path / "router.toml"
    cfg.write_text("[doctranslate]\ntranslator = \"router\"\n", encoding="utf-8")
    p = create_parser()
    args = p.parse_args(
        [
            "--translator",
            "router",
            "--config",
            str(cfg),
            "--files",
            "x.pdf",
        ],
    )
    assert args.translator == "router"
    assert args.validate_translators is False


def test_parser_default_translator_openai():
    p = create_parser()
    args = p.parse_args(["--openai", "--openai-api-key", "k", "--files", "a.pdf"])
    assert args.translator == "openai"
