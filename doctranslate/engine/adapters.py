"""Map stable public schema models to internal runtime types."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from doctranslate.format.pdf.translation_settings import TranslationSettings
from doctranslate.format.pdf.translation_settings import WatermarkOutputMode
from doctranslate.glossary import Glossary
from doctranslate.glossary import GlossaryEntry
from doctranslate.schemas.enums import TranslatorMode
from doctranslate.schemas.public_api import GlossarySpec
from doctranslate.schemas.public_api import OpenAIRequestArgs
from doctranslate.schemas.public_api import TranslationMemorySpec
from doctranslate.schemas.public_api import TranslationOptions
from doctranslate.schemas.public_api import TranslationRequest
from doctranslate.translator.factory import TranslatorBuildResult
from doctranslate.translator.factory import build_translators

logger = logging.getLogger(__name__)


def _watermark_mode(s: str) -> WatermarkOutputMode:
    return {
        "watermarked": WatermarkOutputMode.Watermarked,
        "no_watermark": WatermarkOutputMode.NoWatermark,
        "both": WatermarkOutputMode.Both,
    }[s]


def load_glossaries_from_request(request: TranslationRequest) -> list[Glossary]:
    """Load CSV and inline glossaries from a :class:`~doctranslate.schemas.public_api.TranslationRequest`."""
    glossaries: list[Glossary] = []
    opts = request.options
    spec: GlossarySpec | None = opts.glossary if opts else None
    if not spec:
        return glossaries
    for csv_s in spec.csv_paths:
        p = Path(csv_s)
        if not p.is_file():
            logger.warning("Glossary CSV not found, skipping: %s", p)
            continue
        try:
            g = Glossary.from_csv(p, request.lang_out)
            if g.entries:
                glossaries.append(g)
        except Exception:
            logger.exception("Failed to load glossary from %s", p)
    if spec.inline_entries:
        entries = [
            GlossaryEntry(e.source, e.target, e.target_language)
            for e in spec.inline_entries
        ]
        glossaries.append(Glossary(name=spec.inline_name, entries=entries))
    return glossaries


def translation_settings_from_request(
    request: TranslationRequest,
    *,
    glossaries: list[Glossary],
) -> TranslationSettings:
    """Build :class:`~doctranslate.format.pdf.translation_settings.TranslationSettings` from a public request."""
    opts = request.options or TranslationOptions()
    tm: TranslationMemorySpec = opts.translation_memory or TranslationMemorySpec()
    split_strategy = None
    if opts.max_pages_per_part:
        from doctranslate.format.pdf.translation_config import (  # noqa: PLC0415
            TranslationConfig,
        )

        split_strategy = TranslationConfig.create_max_pages_per_part_split_strategy(
            opts.max_pages_per_part,
        )

    settings = TranslationSettings(
        lang_in=request.lang_in,
        lang_out=request.lang_out,
        pages=opts.pages,
        output_dir=opts.output_dir,
        debug=opts.debug,
        working_dir=opts.working_dir,
        no_dual=opts.no_dual,
        no_mono=opts.no_mono,
        qps=opts.qps,
        report_interval=opts.report_interval,
        watermark_output_mode=_watermark_mode(opts.watermark_output_mode),
        glossaries=glossaries or None,
        auto_extract_glossary=opts.auto_extract_glossary,
        skip_translation=opts.skip_translation,
        only_parse_generate_pdf=opts.only_parse_generate_pdf,
        pool_max_workers=opts.pool_max_workers,
        term_pool_max_workers=opts.term_pool_max_workers,
        llm_translation_batch_max_tokens=opts.llm_translation_batch_max_tokens,
        llm_translation_batch_max_paragraphs=opts.llm_translation_batch_max_paragraphs,
        llm_term_extraction_batch_max_tokens=opts.llm_term_extraction_batch_max_tokens,
        llm_term_extraction_batch_max_paragraphs=opts.llm_term_extraction_batch_max_paragraphs,
        use_rich_pbar=opts.use_rich_pbar,
        metadata_extra_data=opts.metadata_extra_data,
        tm_mode=tm.tm_mode,
        tm_scope=tm.tm_scope,
        tm_min_segment_chars=tm.tm_min_segment_chars,
        tm_fuzzy_min_score=tm.tm_fuzzy_min_score,
        tm_semantic_min_similarity=tm.tm_semantic_min_similarity,
        tm_project_id=tm.tm_project_id,
        tm_embedding_model=tm.tm_embedding_model,
        tm_import_path=tm.tm_import_path,
        tm_export_path=tm.tm_export_path,
        ocr_mode=opts.ocr_mode,
        ocr_pages=opts.ocr_pages,
        ocr_lang_hints=list(opts.ocr_lang_hints),
        ocr_debug_dump=opts.ocr_debug_dump,
        split_strategy=split_strategy,
    )
    return settings


def build_translators_for_request(request: TranslationRequest) -> TranslatorBuildResult:
    """Dispatch translator construction from :class:`~doctranslate.schemas.public_api.TranslatorRequestConfig`."""
    tc = request.translator
    if tc.mode == TranslatorMode.OPENAI:
        oa: OpenAIRequestArgs = tc.openai or OpenAIRequestArgs()
        return build_translators(
            translator_mode="openai",
            config_path=tc.config_path,
            lang_in=request.lang_in,
            lang_out=request.lang_out,
            ignore_cache=tc.ignore_cache,
            openai_args={
                "model": oa.model,
                "base_url": oa.base_url,
                "api_key": oa.api_key,
                "enable_json_mode_if_requested": oa.enable_json_mode_if_requested,
                "send_dashscope_header": oa.send_dashscope_header,
                "send_temperature": oa.send_temperature,
                "reasoning": oa.reasoning,
                "term_model": oa.term_model,
                "term_base_url": oa.term_base_url,
                "term_api_key": oa.term_api_key,
                "term_reasoning": oa.term_reasoning,
            },
        )
    if tc.mode == TranslatorMode.ROUTER:
        return build_translators(
            translator_mode="router",
            config_path=tc.config_path,
            lang_in=request.lang_in,
            lang_out=request.lang_out,
            ignore_cache=tc.ignore_cache,
            cli_router_overrides=tc.cli_router_overrides,
        )
    if tc.mode == TranslatorMode.LOCAL:
        return build_translators(
            translator_mode="local",
            config_path=tc.config_path,
            lang_in=request.lang_in,
            lang_out=request.lang_out,
            ignore_cache=tc.ignore_cache,
            cli_router_overrides=tc.cli_router_overrides,
            local_cli=tc.local_cli or {},
        )
    msg = f"Unsupported translator mode: {tc.mode!r}"
    raise ValueError(msg)


def translation_config_from_request(
    request: TranslationRequest,
    *,
    glossaries: list[Glossary],
    doc_layout_model: Any,
    built: TranslatorBuildResult | None = None,
) -> Any:
    """Build runtime :class:`~doctranslate.format.pdf.translation_config.TranslationConfig`."""
    from doctranslate.format.pdf.translation_config import TranslationConfig

    settings = translation_settings_from_request(
        request,
        glossaries=glossaries,
    )
    resolved = built or build_translators_for_request(request)
    return TranslationConfig.from_settings(
        resolved.translator,
        Path(request.input_pdf),
        doc_layout_model,
        settings,
        term_extraction_translator=resolved.term_extraction_translator,
    )
