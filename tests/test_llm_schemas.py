"""Pydantic schema coercion for LLM structured outputs."""

import json

from doctranslate.translator.llm.schemas import BatchTranslationEnvelope
from doctranslate.translator.llm.schemas import TermExtractionEnvelope


def test_term_extraction_envelope_accepts_bare_list():
    raw = json.dumps([{"src": "A", "tgt": "a"}])
    m = TermExtractionEnvelope.model_validate_json(raw)
    assert len(m.terms) == 1
    assert m.terms[0].src == "A"


def test_term_extraction_envelope_accepts_wrapped_object():
    raw = json.dumps({"terms": [{"src": "X", "tgt": "y"}]})
    m = TermExtractionEnvelope.model_validate_json(raw)
    assert m.terms[0].src == "X"


def test_batch_translation_envelope_accepts_bare_list():
    raw = json.dumps([{"id": 0, "output": "hello"}])
    m = BatchTranslationEnvelope.model_validate_json(raw)
    assert len(m.items) == 1
    assert m.items[0].id == 0


def test_batch_translation_envelope_empty_object_is_valid():
    m = BatchTranslationEnvelope.model_validate_json("{}")
    assert m.items == []
