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


def test_parser_accepts_translator_local_flags():
    p = create_parser()
    args = p.parse_args(
        [
            "--translator",
            "local",
            "--local-model",
            "qwen2.5:7b",
            "--files",
            "x.pdf",
        ],
    )
    assert args.translator == "local"
    assert args.local_model == "qwen2.5:7b"


def test_parser_accepts_ocr_flags():
    p = create_parser()
    args = p.parse_args(
        [
            "--translator",
            "local",
            "--local-model",
            "m",
            "--files",
            "x.pdf",
            "--ocr-mode",
            "hybrid",
            "--ocr-pages",
            "1,3-5",
            "--ocr-lang",
            "en,ja",
            "--ocr-debug",
        ],
    )
    assert args.ocr_mode == "hybrid"
    assert args.ocr_pages == "1,3-5"
    assert args.ocr_lang == "en,ja"
    assert args.ocr_debug is True
