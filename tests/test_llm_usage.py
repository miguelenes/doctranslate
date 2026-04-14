"""Token usage normalization from mocked API responses."""

from unittest.mock import MagicMock

from doctranslate.translator.llm.usage import token_usage_from_chat_completion
from doctranslate.translator.llm.usage import token_usage_from_openai_response


def test_chat_completion_usage_with_cache_details():
    usage = MagicMock()
    usage.prompt_tokens = 10
    usage.completion_tokens = 5
    usage.total_tokens = 15
    usage.prompt_cache_hit_tokens = 2
    details = MagicMock()
    details.cached_tokens = 3
    resp = MagicMock(usage=usage, prompt_tokens_details=details)
    u = token_usage_from_chat_completion(resp)
    assert u.prompt_tokens == 10
    assert u.completion_tokens == 5
    assert u.total_tokens == 15
    assert u.cache_hit_prompt_tokens == 5


def test_openai_response_usage():
    usage = MagicMock()
    usage.input_tokens = 8
    usage.output_tokens = 4
    usage.total_tokens = 12
    details = MagicMock()
    details.cached_tokens = 1
    usage.input_tokens_details = details
    resp = MagicMock(usage=usage)
    u = token_usage_from_openai_response(resp)
    assert u.prompt_tokens == 8
    assert u.completion_tokens == 4
    assert u.total_tokens == 12
    assert u.cache_hit_prompt_tokens == 1
