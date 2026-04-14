"""CLI vNext routing, argv mapping, and parser smoke tests."""

from doctranslate.cli.dispatch import build_vnext_parser
from doctranslate.cli.dispatch import should_use_vnext
from doctranslate.cli.vnext_argv import build_translate_legacy_argv


def test_should_use_vnext_prefers_subcommand():
    assert should_use_vnext(["translate", "a.pdf"]) is True
    assert should_use_vnext(["assets", "warmup"]) is True


def test_should_use_vnext_respects_global_config_before_subcommand():
    assert should_use_vnext(["-c", "x.toml", "translate", "a.pdf"]) is True


def test_legacy_flat_files_triggers_legacy_path():
    assert should_use_vnext(["--files", "a.pdf"]) is False


def test_legacy_openai_flag_triggers_legacy_path():
    assert should_use_vnext(["--openai", "--files", "a.pdf"]) is False


def test_translate_parse_known_passes_unknown_to_legacy_tail():
    p = build_vnext_parser()
    args, unknown = p.parse_known_args(
        [
            "translate",
            "a.pdf",
            "--provider",
            "openai",
            "--ocr-mode",
            "hybrid",
        ],
    )
    assert args.command == "translate"
    assert args.translate_inputs == ["a.pdf"]
    assert args.provider == "openai"
    assert unknown == ["--ocr-mode", "hybrid"]


def test_build_translate_legacy_argv_maps_vnext_names():
    p = build_vnext_parser()
    args, unknown = p.parse_known_args(
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
    args.extra_legacy = unknown
    legacy_argv = build_translate_legacy_argv(args)
    assert "--files" in legacy_argv
    assert "doc.pdf" in legacy_argv
    assert "--translator" in legacy_argv and "router" in legacy_argv
    assert "--lang-in" in legacy_argv and "de" in legacy_argv
    assert "--lang-out" in legacy_argv and "fr" in legacy_argv
    assert "--max-pages-per-part" in legacy_argv and "12" in legacy_argv
    assert "--watermark-output-mode" in legacy_argv and "both" in legacy_argv
