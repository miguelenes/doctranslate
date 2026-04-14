"""CLI routing and parser smoke tests."""

from doctranslate.cli.dispatch import build_vnext_parser


def test_translate_parse_args_accepts_ocr_mode():
    p = build_vnext_parser()
    args = p.parse_args(
        [
            "translate",
            "a.pdf",
            "--translator",
            "openai",
            "--ocr-mode",
            "hybrid",
        ],
    )
    assert args.command == "translate"
    assert args.translate_inputs == ["a.pdf"]
    assert args.translator == "openai"
    assert args.ocr_mode == "hybrid"


def test_translate_parse_args_aliases():
    p = build_vnext_parser()
    args = p.parse_args(
        [
            "translate",
            "doc.pdf",
            "--provider",
            "router",
            "--source-lang",
            "de",
            "--target-lang",
            "fr",
            "--split-pages",
            "12",
            "--watermark-mode",
            "both",
        ],
    )
    assert args.translator == "router"
    assert args.lang_in == "de"
    assert args.lang_out == "fr"
    assert args.max_pages_per_part == 12
    assert args.watermark_output_mode == "both"
