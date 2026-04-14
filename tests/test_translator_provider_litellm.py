"""Tests for LiteLLM provider wrapper (mocked)."""

from unittest.mock import MagicMock, patch

from doctranslate.translator.config import ProviderConfigModel
from doctranslate.translator.providers.litellm_provider import LiteLLMProviderExecutor


@patch("litellm.completion")
def test_litellm_executor_maps_response(mock_completion):
    usage = MagicMock()
    usage.prompt_tokens = 3
    usage.completion_tokens = 7
    usage.total_tokens = 10
    usage.prompt_cache_hit_tokens = 0
    msg = MagicMock()
    msg.content = "  hello  "
    choice = MagicMock()
    choice.message = msg
    mock_completion.return_value = MagicMock(choices=[choice], usage=usage)

    cfg = ProviderConfigModel(provider="openai", model="gpt-4o-mini", api_key="sk-x")
    ex = LiteLLMProviderExecutor("p1", cfg)
    r = ex.complete([{"role": "user", "content": "hi"}], json_mode=False)
    assert r.text == "hello"
    assert r.usage.total_tokens == 10
    mock_completion.assert_called_once()
