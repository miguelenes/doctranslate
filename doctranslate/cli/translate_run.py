"""Legacy translation pipeline and progress UI."""

from __future__ import annotations

import logging
import random
from pathlib import Path
from typing import Any

import tqdm
from rich.progress import BarColumn
from rich.progress import MofNCompleteColumn
from rich.progress import Progress
from rich.progress import TextColumn
from rich.progress import TimeElapsedColumn
from rich.progress import TimeRemainingColumn

import doctranslate.assets.assets
import doctranslate.format.pdf.high_level
from doctranslate.const import enable_process_pool
from doctranslate.format.pdf.translation_config import TranslationConfig
from doctranslate.format.pdf.translation_settings import TranslationSettings
from doctranslate.format.pdf.translation_settings import WatermarkOutputMode
from doctranslate.glossary import Glossary
from doctranslate.translator.config import load_nested_translator_config
from doctranslate.translator.config import merge_cli_router_overrides_from_mapping
from doctranslate.translator.config import validate_router_config
from doctranslate.translator.factory import build_translators
from doctranslate.translator.factory import resolve_openai_api_key
from doctranslate.translator.local_config import (
    convert_local_translator_to_router_nested,
)
from doctranslate.translator.local_config import local_cli_dict_from_args
from doctranslate.translator.local_config import merge_local_cli_into_nested
from doctranslate.translator.local_config import validate_local_nested
from doctranslate.translator.providers.local_preflight import LocalPreflightError
from doctranslate.translator.providers.local_preflight import run_local_preflight
from doctranslate.translator.translator import set_translate_rate_limiter

logger = logging.getLogger(__name__)


def _llm_batch_kwargs_for_translation_config(
    args: Any,
    nested_cfg: Any | None,
) -> dict[str, Any | None]:
    """Resolve LLM batch limits from CLI or nested translator config (local mode)."""
    out: dict[str, Any | None] = {
        "llm_translation_batch_max_tokens": None,
        "llm_translation_batch_max_paragraphs": None,
        "llm_term_extraction_batch_max_tokens": None,
        "llm_term_extraction_batch_max_paragraphs": None,
    }
    pairs = (
        ("local_translation_batch_tokens", "llm_translation_batch_max_tokens"),
        ("local_translation_batch_paragraphs", "llm_translation_batch_max_paragraphs"),
        ("local_term_batch_tokens", "llm_term_extraction_batch_max_tokens"),
        ("local_term_batch_paragraphs", "llm_term_extraction_batch_max_paragraphs"),
    )
    for arg_attr, out_key in pairs:
        v = getattr(args, arg_attr, None)
        if v is not None:
            out[out_key] = v
            continue
        if nested_cfg is not None:
            nv = getattr(nested_cfg, arg_attr, None)
            if nv is not None:
                out[out_key] = nv
    return out


def _cli_router_override_dict(args: Any) -> dict[str, Any]:
    """Build optional CLI overrides for nested router TOML."""
    out: dict[str, Any] = {}
    if getattr(args, "routing_profile", None):
        out["routing_profile"] = args.routing_profile
    if getattr(args, "term_extraction_profile", None):
        out["term_extraction_profile"] = args.term_extraction_profile
    if getattr(args, "routing_strategy", None):
        out["routing_strategy"] = args.routing_strategy
    if getattr(args, "metrics_output", None):
        out["metrics_output"] = args.metrics_output
    if getattr(args, "metrics_json_path", None):
        out["metrics_json_path"] = args.metrics_json_path
    return out


async def run_legacy_translate_pipeline(parser: Any, args: Any) -> None:
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.generate_offline_assets:
        doctranslate.assets.assets.generate_offline_assets_package(
            Path(args.generate_offline_assets)
        )
        logger.info("Offline assets package generated, exiting...")
        return

    if args.restore_offline_assets:
        doctranslate.assets.assets.restore_offline_assets_package(
            Path(args.restore_offline_assets)
        )
        logger.info("Offline assets package restored, exiting...")
        return

    if args.warmup:
        doctranslate.assets.assets.warmup()
        logger.info("Warmup completed, exiting...")
        return

    if getattr(args, "validate_translators", False):
        if args.translator == "router":
            if not args.config:
                parser.error("Router validation requires --config")
            nested = load_nested_translator_config(Path(args.config))
            overrides = _cli_router_override_dict(args)
            nested = merge_cli_router_overrides_from_mapping(nested, overrides)
            validate_router_config(nested)
            logger.info("Translator configuration is valid.")
            return
        if args.translator == "local":
            nested = load_nested_translator_config(
                Path(args.config) if args.config else None,
            )
            nested = merge_local_cli_into_nested(nested, local_cli_dict_from_args(args))
            nested = nested.model_copy(update={"translator": "local"})
            err = validate_local_nested(nested)
            if err:
                parser.error(err)
            try:
                run_local_preflight(nested)
            except LocalPreflightError as e:
                parser.error(str(e))
            converted = convert_local_translator_to_router_nested(nested)
            validate_router_config(converted)
            logger.info(
                "Local translator configuration is valid and preflight succeeded."
            )
            return
        parser.error(
            "--validate-translators requires --translator router or --translator local"
        )

    if args.translator == "openai":
        if not args.openai and not getattr(args, "openai_implicit", False):
            parser.error(
                "OpenAI translator requires --openai (legacy) or "
                "`doctranslate translate --provider openai` (vNext).",
            )
        api_key = resolve_openai_api_key(args.openai_api_key)
        if not api_key:
            parser.error(
                "OpenAI mode requires an API key: pass --openai-api-key / -k "
                "or set OPENAI_API_KEY in the environment.",
            )
        args.openai_api_key = api_key
    elif args.translator == "router":
        if not args.config:
            parser.error(
                "Router mode requires --config with [doctranslate] providers and profiles",
            )
    elif args.translator == "local":
        nested_chk = load_nested_translator_config(
            Path(args.config) if args.config else None,
        )
        nested_chk = merge_local_cli_into_nested(
            nested_chk,
            local_cli_dict_from_args(args),
        )
        nested_chk = nested_chk.model_copy(update={"translator": "local"})
        err = validate_local_nested(nested_chk)
        if err:
            parser.error(err)
        try:
            run_local_preflight(nested_chk)
        except LocalPreflightError as e:
            parser.error(str(e))
    else:
        parser.error(f"Unknown translator mode: {args.translator}")

    if args.enable_process_pool:
        enable_process_pool()

    if args.translator == "openai":
        translator_kwargs: dict[str, Any] = {}
        if args.openai_reasoning is not None:
            translator_kwargs["reasoning"] = args.openai_reasoning
        built = build_translators(
            translator_mode="openai",
            config_path=args.config,
            lang_in=args.lang_in,
            lang_out=args.lang_out,
            ignore_cache=args.ignore_cache,
            openai_args={
                "model": args.openai_model,
                "base_url": args.openai_base_url,
                "api_key": args.openai_api_key,
                "enable_json_mode_if_requested": args.enable_json_mode_if_requested,
                "send_dashscope_header": args.send_dashscope_header,
                "send_temperature": not args.no_send_temperature,
                "reasoning": args.openai_reasoning,
                "term_model": args.openai_term_extraction_model,
                "term_base_url": args.openai_term_extraction_base_url,
                "term_api_key": args.openai_term_extraction_api_key,
                "term_reasoning": args.openai_term_extraction_reasoning,
            },
        )
    elif args.translator == "local":
        overrides = _cli_router_override_dict(args)
        built = build_translators(
            translator_mode="local",
            config_path=args.config,
            lang_in=args.lang_in,
            lang_out=args.lang_out,
            ignore_cache=args.ignore_cache,
            cli_router_overrides=overrides or None,
            local_cli=local_cli_dict_from_args(args),
        )
    else:
        overrides = _cli_router_override_dict(args)
        built = build_translators(
            translator_mode="router",
            config_path=args.config,
            lang_in=args.lang_in,
            lang_out=args.lang_out,
            ignore_cache=args.ignore_cache,
            cli_router_overrides=overrides or None,
        )
    translator = built.translator
    term_extraction_translator = built.term_extraction_translator
    llm_batch_kwargs = _llm_batch_kwargs_for_translation_config(
        args,
        built.nested_config,
    )

    # 设置翻译速率限制
    set_translate_rate_limiter(args.qps)
    # 初始化文档布局模型
    if args.rpc_doclayout:
        from doctranslate.docvision.rpc_doclayout import RpcDocLayoutModel

        doc_layout_model = RpcDocLayoutModel(host=args.rpc_doclayout)
    elif args.rpc_doclayout2:
        from doctranslate.docvision.rpc_doclayout2 import RpcDocLayoutModel

        doc_layout_model = RpcDocLayoutModel(host=args.rpc_doclayout2)
    elif args.rpc_doclayout3:
        from doctranslate.docvision.rpc_doclayout3 import RpcDocLayoutModel

        doc_layout_model = RpcDocLayoutModel(host=args.rpc_doclayout3)
    elif args.rpc_doclayout4:
        from doctranslate.docvision.rpc_doclayout4 import RpcDocLayoutModel

        doc_layout_model = RpcDocLayoutModel(host=args.rpc_doclayout4)
    elif args.rpc_doclayout5:
        from doctranslate.docvision.rpc_doclayout5 import RpcDocLayoutModel

        doc_layout_model = RpcDocLayoutModel(host=args.rpc_doclayout5)
    elif args.rpc_doclayout6:
        from doctranslate.docvision.rpc_doclayout6 import RpcDocLayoutModel

        doc_layout_model = RpcDocLayoutModel(host=args.rpc_doclayout6)
    elif args.rpc_doclayout7:
        from doctranslate.docvision.rpc_doclayout7 import RpcDocLayoutModel

        doc_layout_model = RpcDocLayoutModel(host=args.rpc_doclayout7)
    else:
        from doctranslate.docvision.doclayout import DocLayoutModel

        doc_layout_model = DocLayoutModel.load_onnx()

    if args.translate_table_text:
        from doctranslate.docvision.table_detection.rapidocr import RapidOCRModel

        table_model = RapidOCRModel()
    else:
        table_model = None

    # Load glossaries
    loaded_glossaries: list[Glossary] = []
    if args.glossary_files:
        paths_str = args.glossary_files.split(",")
        for p_str in paths_str:
            file_path = Path(p_str.strip())
            if not file_path.exists():
                logger.error(f"Glossary file not found: {file_path}")
                continue
            if not file_path.is_file():
                logger.error(f"Glossary path is not a file: {file_path}")
                continue
            try:
                glossary_obj = Glossary.from_csv(file_path, args.lang_out)
                if glossary_obj.entries:
                    loaded_glossaries.append(glossary_obj)
                    logger.info(
                        f"Loaded glossary '{glossary_obj.name}' with {len(glossary_obj.entries)} entries."
                    )
                else:
                    logger.info(
                        f"Glossary '{file_path.stem}' loaded with no applicable entries for lang_out '{args.lang_out}'."
                    )
            except Exception as e:
                logger.error(f"Failed to load glossary from {file_path}: {e}")

    pending_files = []
    for file in args.files:
        # 清理文件路径，去除两端的引号
        if file.startswith("--files="):
            file = file[len("--files=") :]
        file = file.lstrip("-").strip("\"'")
        if not Path(file).exists():
            logger.error("File does not exist: %s", file)
            exit(1)
        if not file.lower().endswith(".pdf"):
            logger.error("Not a PDF file: %s", file)
            exit(1)
        pending_files.append(file)

    if args.output:
        if not Path(args.output).exists():
            logger.info("Output directory does not exist; creating: %s", args.output)
            try:
                Path(args.output).mkdir(parents=True, exist_ok=True)
            except OSError:
                logger.critical(
                    f"Failed to create output folder at {args.output}",
                    exc_info=True,
                )
                exit(1)
    else:
        args.output = None

    if args.working_dir:
        working_dir = Path(args.working_dir)
        if not working_dir.exists():
            logger.info("Working directory does not exist; creating: %s", working_dir)
            try:
                working_dir.mkdir(parents=True, exist_ok=True)
            except OSError:
                logger.critical(
                    f"Failed to create working directory at {working_dir}",
                    exc_info=True,
                )
                exit(1)
    else:
        working_dir = None

    watermark_output_mode = WatermarkOutputMode.Watermarked
    if args.no_watermark:
        watermark_output_mode = WatermarkOutputMode.NoWatermark
    elif args.watermark_output_mode == "both":
        watermark_output_mode = WatermarkOutputMode.Both
    elif args.watermark_output_mode == "watermarked":
        watermark_output_mode = WatermarkOutputMode.Watermarked
    elif args.watermark_output_mode == "no_watermark":
        watermark_output_mode = WatermarkOutputMode.NoWatermark

    split_strategy = None
    if args.max_pages_per_part:
        split_strategy = TranslationConfig.create_max_pages_per_part_split_strategy(
            args.max_pages_per_part
        )

    total_term_extraction_total_tokens = 0
    total_term_extraction_prompt_tokens = 0
    total_term_extraction_completion_tokens = 0
    total_term_extraction_cache_hit_prompt_tokens = 0

    ocr_lang_hints: list[str] = []
    if getattr(args, "ocr_lang", None):
        ocr_lang_hints = [x.strip() for x in args.ocr_lang.split(",") if x.strip()]

    job_settings = TranslationSettings(
        lang_in=args.lang_in,
        lang_out=args.lang_out,
        pages=args.pages,
        output_dir=args.output,
        debug=args.debug,
        working_dir=working_dir,
        no_dual=args.no_dual,
        no_mono=args.no_mono,
        formular_font_pattern=args.formular_font_pattern,
        formular_char_pattern=args.formular_char_pattern,
        qps=args.qps,
        split_short_lines=args.split_short_lines,
        short_line_split_factor=args.short_line_split_factor,
        skip_clean=args.skip_clean,
        dual_translate_first=args.dual_translate_first,
        disable_rich_text_translate=args.disable_rich_text_translate,
        report_interval=args.report_interval,
        min_text_length=args.min_text_length,
        use_alternating_pages_dual=args.use_alternating_pages_dual,
        watermark_output_mode=watermark_output_mode,
        split_strategy=split_strategy,
        table_model=table_model,
        show_char_box=args.show_char_box,
        skip_scanned_detection=args.skip_scanned_detection,
        ocr_workaround=args.ocr_workaround,
        custom_system_prompt=args.custom_system_prompt,
        add_formula_placehold_hint=args.add_formula_placehold_hint,
        disable_same_text_fallback=args.disable_same_text_fallback,
        glossaries=loaded_glossaries,
        pool_max_workers=args.pool_max_workers,
        auto_extract_glossary=args.auto_extract_glossary,
        auto_enable_ocr_workaround=args.auto_enable_ocr_workaround,
        primary_font_family=args.primary_font_family,
        only_include_translated_page=args.only_include_translated_page,
        save_auto_extracted_glossary=args.save_auto_extracted_glossary,
        enable_graphic_element_process=not args.disable_graphic_element_process,
        merge_alternating_line_numbers=args.merge_alternating_line_numbers,
        skip_translation=args.skip_translation,
        skip_form_render=args.skip_form_render,
        skip_curve_render=args.skip_curve_render,
        only_parse_generate_pdf=args.only_parse_generate_pdf,
        remove_non_formula_lines=args.remove_non_formula_lines,
        non_formula_line_iou_threshold=args.non_formula_line_iou_threshold,
        figure_table_protection_threshold=args.figure_table_protection_threshold,
        skip_formula_offset_calculation=args.skip_formula_offset_calculation,
        metadata_extra_data=args.metadata_extra_data,
        term_pool_max_workers=args.term_pool_max_workers,
        llm_translation_batch_max_tokens=llm_batch_kwargs[
            "llm_translation_batch_max_tokens"
        ],
        llm_translation_batch_max_paragraphs=llm_batch_kwargs[
            "llm_translation_batch_max_paragraphs"
        ],
        llm_term_extraction_batch_max_tokens=llm_batch_kwargs[
            "llm_term_extraction_batch_max_tokens"
        ],
        llm_term_extraction_batch_max_paragraphs=llm_batch_kwargs[
            "llm_term_extraction_batch_max_paragraphs"
        ],
        tm_mode=args.tm_mode,
        tm_scope=args.tm_scope,
        tm_min_segment_chars=args.tm_min_segment_chars,
        tm_fuzzy_min_score=args.tm_fuzzy_min_score,
        tm_semantic_min_similarity=args.tm_semantic_min_similarity,
        tm_project_id=args.tm_project_id,
        tm_embedding_model=args.tm_embedding_model,
        tm_import_path=args.tm_import_path,
        tm_export_path=args.tm_export_path,
        ocr_mode=args.ocr_mode,
        ocr_pages=args.ocr_pages,
        ocr_lang_hints=ocr_lang_hints,
        ocr_debug_dump=args.ocr_debug,
    )

    for file in pending_files:
        # 清理文件路径，去除两端的引号
        file = file.strip("\"'")
        config = TranslationConfig(
            translator,
            file,
            doc_layout_model,
            job_settings,
            term_extraction_translator=term_extraction_translator,
        )

        def nop(_x):
            pass

        getattr(doc_layout_model, "init_font_mapper", nop)(config)
        # Create progress handler
        progress_context, progress_handler = create_progress_handler(
            config, show_log=False
        )

        # 开始翻译
        with progress_context:
            async for event in doctranslate.format.pdf.high_level.async_translate(
                config
            ):
                progress_handler(event)
                if config.debug:
                    logger.debug(event)
                if event["type"] == "error":
                    logger.error(f"Error: {event['error']}")
                    break
                if event["type"] == "finish":
                    result = event["translate_result"]
                    logger.info(str(result))
                    config.run_tm_export_if_configured()
                    break
        usage = config.term_extraction_token_usage
        total_term_extraction_total_tokens += usage["total_tokens"]
        total_term_extraction_prompt_tokens += usage["prompt_tokens"]
        total_term_extraction_completion_tokens += usage["completion_tokens"]
        total_term_extraction_cache_hit_prompt_tokens += usage[
            "cache_hit_prompt_tokens"
        ]
    logger.info(f"Total tokens: {translator.token_count.value}")
    logger.info(f"Prompt tokens: {translator.prompt_token_count.value}")
    logger.info(f"Completion tokens: {translator.completion_token_count.value}")
    logger.info(
        f"Cache hit prompt tokens: {translator.cache_hit_prompt_token_count.value}"
    )
    logger.info(
        "Term extraction tokens: total=%s prompt=%s completion=%s cache_hit_prompt=%s",
        total_term_extraction_total_tokens,
        total_term_extraction_prompt_tokens,
        total_term_extraction_completion_tokens,
        total_term_extraction_cache_hit_prompt_tokens,
    )
    if term_extraction_translator is not translator:
        logger.info(
            "Term extraction translator raw tokens: total=%s prompt=%s completion=%s cache_hit_prompt=%s",
            term_extraction_translator.token_count.value,
            term_extraction_translator.prompt_token_count.value,
            term_extraction_translator.completion_token_count.value,
            term_extraction_translator.cache_hit_prompt_token_count.value,
        )
    if hasattr(translator, "print_metrics"):
        logger.info("%s", translator.print_metrics())
    if term_extraction_translator is not translator and hasattr(
        term_extraction_translator,
        "print_metrics",
    ):
        logger.info(
            "Term extraction metrics:\n%s", term_extraction_translator.print_metrics()
        )
    if hasattr(translator, "flush_metrics_json") and getattr(
        args,
        "metrics_json_path",
        None,
    ):
        translator.flush_metrics_json(args.metrics_json_path)


def create_progress_handler(
    translation_config: TranslationConfig, show_log: bool = False
):
    """Create a progress handler function based on the configuration.

    Args:
        translation_config: The translation configuration.

    Returns:
        A tuple of (progress_context, progress_handler), where progress_context is a context
        manager that should be used to wrap the translation process, and progress_handler
        is a function that will be called with progress events.
    """
    if translation_config.use_rich_pbar:
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        )
        translate_task_id = progress.add_task("translate", total=100)
        stage_tasks = {}

        def progress_handler(event):
            if show_log and random.random() <= 0.1:  # noqa: S311
                logger.info(event)
            if event["type"] == "progress_start":
                if event["stage"] not in stage_tasks:
                    stage_tasks[event["stage"]] = progress.add_task(
                        f"{event['stage']} ({event['part_index']}/{event['total_parts']})",
                        total=event.get("stage_total", 100),
                    )
            elif event["type"] == "progress_update":
                stage = event["stage"]
                if stage in stage_tasks:
                    progress.update(
                        stage_tasks[stage],
                        completed=event["stage_current"],
                        total=event["stage_total"],
                        description=f"{event['stage']} ({event['part_index']}/{event['total_parts']})",
                        refresh=True,
                    )
                progress.update(
                    translate_task_id,
                    completed=event["overall_progress"],
                    refresh=True,
                )
            elif event["type"] == "progress_end":
                stage = event["stage"]
                if stage in stage_tasks:
                    progress.update(
                        stage_tasks[stage],
                        completed=event["stage_total"],
                        total=event["stage_total"],
                        description=f"{event['stage']} ({event['part_index']}/{event['total_parts']})",
                        refresh=True,
                    )
                    progress.update(
                        translate_task_id,
                        completed=event["overall_progress"],
                        refresh=True,
                    )
                progress.refresh()

        return progress, progress_handler
    else:
        pbar = tqdm.tqdm(total=100, desc="translate")

        def progress_handler(event):
            if event["type"] == "progress_update":
                pbar.update(event["overall_progress"] - pbar.n)
                pbar.set_description(
                    f"{event['stage']} ({event['stage_current']}/{event['stage_total']})",
                )
            elif event["type"] == "progress_end":
                pbar.set_description(f"{event['stage']} (Complete)")
                pbar.refresh()

        return pbar, progress_handler
