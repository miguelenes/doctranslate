from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.translation_options_ocr_mode import TranslationOptionsOcrMode, check_translation_options_ocr_mode
from ..models.translation_options_watermark_output_mode import (
    TranslationOptionsWatermarkOutputMode,
    check_translation_options_watermark_output_mode,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.glossary_spec import GlossarySpec
    from ..models.translation_memory_spec import TranslationMemorySpec


T = TypeVar("T", bound="TranslationOptions")


@_attrs_define
class TranslationOptions:
    """PDF/runtime options (optional; defaults match engine defaults).

    Attributes:
        auto_extract_glossary (bool | Unset):  Default: True.
        debug (bool | Unset):  Default: False.
        glossary (GlossarySpec | None | Unset):
        llm_term_extraction_batch_max_paragraphs (int | None | Unset):
        llm_term_extraction_batch_max_tokens (int | None | Unset):
        llm_translation_batch_max_paragraphs (int | None | Unset):
        llm_translation_batch_max_tokens (int | None | Unset):
        max_pages_per_part (int | None | Unset):
        metadata_extra_data (None | str | Unset):
        no_dual (bool | Unset):  Default: False.
        no_mono (bool | Unset):  Default: False.
        ocr_debug_dump (bool | Unset):  Default: False.
        ocr_lang_hints (list[str] | Unset):
        ocr_mode (TranslationOptionsOcrMode | Unset):  Default: 'off'.
        ocr_pages (None | str | Unset):
        only_parse_generate_pdf (bool | Unset):  Default: False.
        output_dir (None | str | Unset):
        pages (None | str | Unset):
        pool_max_workers (int | None | Unset):
        qps (int | Unset):  Default: 4.
        report_interval (float | Unset):  Default: 0.1.
        skip_translation (bool | Unset):  Default: False.
        term_pool_max_workers (int | None | Unset):
        translation_memory (None | TranslationMemorySpec | Unset):
        use_rich_pbar (bool | Unset):  Default: True.
        watermark_output_mode (TranslationOptionsWatermarkOutputMode | Unset):  Default: 'watermarked'.
        working_dir (None | str | Unset):
    """

    auto_extract_glossary: bool | Unset = True
    debug: bool | Unset = False
    glossary: GlossarySpec | None | Unset = UNSET
    llm_term_extraction_batch_max_paragraphs: int | None | Unset = UNSET
    llm_term_extraction_batch_max_tokens: int | None | Unset = UNSET
    llm_translation_batch_max_paragraphs: int | None | Unset = UNSET
    llm_translation_batch_max_tokens: int | None | Unset = UNSET
    max_pages_per_part: int | None | Unset = UNSET
    metadata_extra_data: None | str | Unset = UNSET
    no_dual: bool | Unset = False
    no_mono: bool | Unset = False
    ocr_debug_dump: bool | Unset = False
    ocr_lang_hints: list[str] | Unset = UNSET
    ocr_mode: TranslationOptionsOcrMode | Unset = "off"
    ocr_pages: None | str | Unset = UNSET
    only_parse_generate_pdf: bool | Unset = False
    output_dir: None | str | Unset = UNSET
    pages: None | str | Unset = UNSET
    pool_max_workers: int | None | Unset = UNSET
    qps: int | Unset = 4
    report_interval: float | Unset = 0.1
    skip_translation: bool | Unset = False
    term_pool_max_workers: int | None | Unset = UNSET
    translation_memory: None | TranslationMemorySpec | Unset = UNSET
    use_rich_pbar: bool | Unset = True
    watermark_output_mode: TranslationOptionsWatermarkOutputMode | Unset = "watermarked"
    working_dir: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.glossary_spec import GlossarySpec
        from ..models.translation_memory_spec import TranslationMemorySpec

        auto_extract_glossary = self.auto_extract_glossary

        debug = self.debug

        glossary: dict[str, Any] | None | Unset
        if isinstance(self.glossary, Unset):
            glossary = UNSET
        elif isinstance(self.glossary, GlossarySpec):
            glossary = self.glossary.to_dict()
        else:
            glossary = self.glossary

        llm_term_extraction_batch_max_paragraphs: int | None | Unset
        if isinstance(self.llm_term_extraction_batch_max_paragraphs, Unset):
            llm_term_extraction_batch_max_paragraphs = UNSET
        else:
            llm_term_extraction_batch_max_paragraphs = self.llm_term_extraction_batch_max_paragraphs

        llm_term_extraction_batch_max_tokens: int | None | Unset
        if isinstance(self.llm_term_extraction_batch_max_tokens, Unset):
            llm_term_extraction_batch_max_tokens = UNSET
        else:
            llm_term_extraction_batch_max_tokens = self.llm_term_extraction_batch_max_tokens

        llm_translation_batch_max_paragraphs: int | None | Unset
        if isinstance(self.llm_translation_batch_max_paragraphs, Unset):
            llm_translation_batch_max_paragraphs = UNSET
        else:
            llm_translation_batch_max_paragraphs = self.llm_translation_batch_max_paragraphs

        llm_translation_batch_max_tokens: int | None | Unset
        if isinstance(self.llm_translation_batch_max_tokens, Unset):
            llm_translation_batch_max_tokens = UNSET
        else:
            llm_translation_batch_max_tokens = self.llm_translation_batch_max_tokens

        max_pages_per_part: int | None | Unset
        if isinstance(self.max_pages_per_part, Unset):
            max_pages_per_part = UNSET
        else:
            max_pages_per_part = self.max_pages_per_part

        metadata_extra_data: None | str | Unset
        if isinstance(self.metadata_extra_data, Unset):
            metadata_extra_data = UNSET
        else:
            metadata_extra_data = self.metadata_extra_data

        no_dual = self.no_dual

        no_mono = self.no_mono

        ocr_debug_dump = self.ocr_debug_dump

        ocr_lang_hints: list[str] | Unset = UNSET
        if not isinstance(self.ocr_lang_hints, Unset):
            ocr_lang_hints = self.ocr_lang_hints

        ocr_mode: str | Unset = UNSET
        if not isinstance(self.ocr_mode, Unset):
            ocr_mode = self.ocr_mode

        ocr_pages: None | str | Unset
        if isinstance(self.ocr_pages, Unset):
            ocr_pages = UNSET
        else:
            ocr_pages = self.ocr_pages

        only_parse_generate_pdf = self.only_parse_generate_pdf

        output_dir: None | str | Unset
        if isinstance(self.output_dir, Unset):
            output_dir = UNSET
        else:
            output_dir = self.output_dir

        pages: None | str | Unset
        if isinstance(self.pages, Unset):
            pages = UNSET
        else:
            pages = self.pages

        pool_max_workers: int | None | Unset
        if isinstance(self.pool_max_workers, Unset):
            pool_max_workers = UNSET
        else:
            pool_max_workers = self.pool_max_workers

        qps = self.qps

        report_interval = self.report_interval

        skip_translation = self.skip_translation

        term_pool_max_workers: int | None | Unset
        if isinstance(self.term_pool_max_workers, Unset):
            term_pool_max_workers = UNSET
        else:
            term_pool_max_workers = self.term_pool_max_workers

        translation_memory: dict[str, Any] | None | Unset
        if isinstance(self.translation_memory, Unset):
            translation_memory = UNSET
        elif isinstance(self.translation_memory, TranslationMemorySpec):
            translation_memory = self.translation_memory.to_dict()
        else:
            translation_memory = self.translation_memory

        use_rich_pbar = self.use_rich_pbar

        watermark_output_mode: str | Unset = UNSET
        if not isinstance(self.watermark_output_mode, Unset):
            watermark_output_mode = self.watermark_output_mode

        working_dir: None | str | Unset
        if isinstance(self.working_dir, Unset):
            working_dir = UNSET
        else:
            working_dir = self.working_dir

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if auto_extract_glossary is not UNSET:
            field_dict["auto_extract_glossary"] = auto_extract_glossary
        if debug is not UNSET:
            field_dict["debug"] = debug
        if glossary is not UNSET:
            field_dict["glossary"] = glossary
        if llm_term_extraction_batch_max_paragraphs is not UNSET:
            field_dict["llm_term_extraction_batch_max_paragraphs"] = llm_term_extraction_batch_max_paragraphs
        if llm_term_extraction_batch_max_tokens is not UNSET:
            field_dict["llm_term_extraction_batch_max_tokens"] = llm_term_extraction_batch_max_tokens
        if llm_translation_batch_max_paragraphs is not UNSET:
            field_dict["llm_translation_batch_max_paragraphs"] = llm_translation_batch_max_paragraphs
        if llm_translation_batch_max_tokens is not UNSET:
            field_dict["llm_translation_batch_max_tokens"] = llm_translation_batch_max_tokens
        if max_pages_per_part is not UNSET:
            field_dict["max_pages_per_part"] = max_pages_per_part
        if metadata_extra_data is not UNSET:
            field_dict["metadata_extra_data"] = metadata_extra_data
        if no_dual is not UNSET:
            field_dict["no_dual"] = no_dual
        if no_mono is not UNSET:
            field_dict["no_mono"] = no_mono
        if ocr_debug_dump is not UNSET:
            field_dict["ocr_debug_dump"] = ocr_debug_dump
        if ocr_lang_hints is not UNSET:
            field_dict["ocr_lang_hints"] = ocr_lang_hints
        if ocr_mode is not UNSET:
            field_dict["ocr_mode"] = ocr_mode
        if ocr_pages is not UNSET:
            field_dict["ocr_pages"] = ocr_pages
        if only_parse_generate_pdf is not UNSET:
            field_dict["only_parse_generate_pdf"] = only_parse_generate_pdf
        if output_dir is not UNSET:
            field_dict["output_dir"] = output_dir
        if pages is not UNSET:
            field_dict["pages"] = pages
        if pool_max_workers is not UNSET:
            field_dict["pool_max_workers"] = pool_max_workers
        if qps is not UNSET:
            field_dict["qps"] = qps
        if report_interval is not UNSET:
            field_dict["report_interval"] = report_interval
        if skip_translation is not UNSET:
            field_dict["skip_translation"] = skip_translation
        if term_pool_max_workers is not UNSET:
            field_dict["term_pool_max_workers"] = term_pool_max_workers
        if translation_memory is not UNSET:
            field_dict["translation_memory"] = translation_memory
        if use_rich_pbar is not UNSET:
            field_dict["use_rich_pbar"] = use_rich_pbar
        if watermark_output_mode is not UNSET:
            field_dict["watermark_output_mode"] = watermark_output_mode
        if working_dir is not UNSET:
            field_dict["working_dir"] = working_dir

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.glossary_spec import GlossarySpec
        from ..models.translation_memory_spec import TranslationMemorySpec

        d = dict(src_dict)
        auto_extract_glossary = d.pop("auto_extract_glossary", UNSET)

        debug = d.pop("debug", UNSET)

        def _parse_glossary(data: object) -> GlossarySpec | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                glossary_type_0 = GlossarySpec.from_dict(data)

                return glossary_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(GlossarySpec | None | Unset, data)

        glossary = _parse_glossary(d.pop("glossary", UNSET))

        def _parse_llm_term_extraction_batch_max_paragraphs(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        llm_term_extraction_batch_max_paragraphs = _parse_llm_term_extraction_batch_max_paragraphs(
            d.pop("llm_term_extraction_batch_max_paragraphs", UNSET)
        )

        def _parse_llm_term_extraction_batch_max_tokens(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        llm_term_extraction_batch_max_tokens = _parse_llm_term_extraction_batch_max_tokens(
            d.pop("llm_term_extraction_batch_max_tokens", UNSET)
        )

        def _parse_llm_translation_batch_max_paragraphs(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        llm_translation_batch_max_paragraphs = _parse_llm_translation_batch_max_paragraphs(
            d.pop("llm_translation_batch_max_paragraphs", UNSET)
        )

        def _parse_llm_translation_batch_max_tokens(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        llm_translation_batch_max_tokens = _parse_llm_translation_batch_max_tokens(
            d.pop("llm_translation_batch_max_tokens", UNSET)
        )

        def _parse_max_pages_per_part(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        max_pages_per_part = _parse_max_pages_per_part(d.pop("max_pages_per_part", UNSET))

        def _parse_metadata_extra_data(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        metadata_extra_data = _parse_metadata_extra_data(d.pop("metadata_extra_data", UNSET))

        no_dual = d.pop("no_dual", UNSET)

        no_mono = d.pop("no_mono", UNSET)

        ocr_debug_dump = d.pop("ocr_debug_dump", UNSET)

        ocr_lang_hints = cast(list[str], d.pop("ocr_lang_hints", UNSET))

        _ocr_mode = d.pop("ocr_mode", UNSET)
        ocr_mode: TranslationOptionsOcrMode | Unset
        if isinstance(_ocr_mode, Unset):
            ocr_mode = UNSET
        else:
            ocr_mode = check_translation_options_ocr_mode(_ocr_mode)

        def _parse_ocr_pages(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        ocr_pages = _parse_ocr_pages(d.pop("ocr_pages", UNSET))

        only_parse_generate_pdf = d.pop("only_parse_generate_pdf", UNSET)

        def _parse_output_dir(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        output_dir = _parse_output_dir(d.pop("output_dir", UNSET))

        def _parse_pages(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        pages = _parse_pages(d.pop("pages", UNSET))

        def _parse_pool_max_workers(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        pool_max_workers = _parse_pool_max_workers(d.pop("pool_max_workers", UNSET))

        qps = d.pop("qps", UNSET)

        report_interval = d.pop("report_interval", UNSET)

        skip_translation = d.pop("skip_translation", UNSET)

        def _parse_term_pool_max_workers(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        term_pool_max_workers = _parse_term_pool_max_workers(d.pop("term_pool_max_workers", UNSET))

        def _parse_translation_memory(data: object) -> None | TranslationMemorySpec | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                translation_memory_type_0 = TranslationMemorySpec.from_dict(data)

                return translation_memory_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TranslationMemorySpec | Unset, data)

        translation_memory = _parse_translation_memory(d.pop("translation_memory", UNSET))

        use_rich_pbar = d.pop("use_rich_pbar", UNSET)

        _watermark_output_mode = d.pop("watermark_output_mode", UNSET)
        watermark_output_mode: TranslationOptionsWatermarkOutputMode | Unset
        if isinstance(_watermark_output_mode, Unset):
            watermark_output_mode = UNSET
        else:
            watermark_output_mode = check_translation_options_watermark_output_mode(_watermark_output_mode)

        def _parse_working_dir(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        working_dir = _parse_working_dir(d.pop("working_dir", UNSET))

        translation_options = cls(
            auto_extract_glossary=auto_extract_glossary,
            debug=debug,
            glossary=glossary,
            llm_term_extraction_batch_max_paragraphs=llm_term_extraction_batch_max_paragraphs,
            llm_term_extraction_batch_max_tokens=llm_term_extraction_batch_max_tokens,
            llm_translation_batch_max_paragraphs=llm_translation_batch_max_paragraphs,
            llm_translation_batch_max_tokens=llm_translation_batch_max_tokens,
            max_pages_per_part=max_pages_per_part,
            metadata_extra_data=metadata_extra_data,
            no_dual=no_dual,
            no_mono=no_mono,
            ocr_debug_dump=ocr_debug_dump,
            ocr_lang_hints=ocr_lang_hints,
            ocr_mode=ocr_mode,
            ocr_pages=ocr_pages,
            only_parse_generate_pdf=only_parse_generate_pdf,
            output_dir=output_dir,
            pages=pages,
            pool_max_workers=pool_max_workers,
            qps=qps,
            report_interval=report_interval,
            skip_translation=skip_translation,
            term_pool_max_workers=term_pool_max_workers,
            translation_memory=translation_memory,
            use_rich_pbar=use_rich_pbar,
            watermark_output_mode=watermark_output_mode,
            working_dir=working_dir,
        )

        return translation_options
