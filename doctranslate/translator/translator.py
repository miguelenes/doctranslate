import contextlib
import logging
import threading
import time
import unicodedata
from abc import ABC
from abc import abstractmethod

import httpx
import openai
from tenacity import before_sleep_log
from tenacity import retry
from tenacity import retry_if_exception_type
from tenacity import stop_after_attempt
from tenacity import wait_exponential

from doctranslate.translator.cache import TranslationCache
from doctranslate.translator.llm.prompt_versions import PROMPT_VERSION_SIMPLE_TRANSLATE
from doctranslate.translator.llm.usage import token_usage_from_chat_completion
from doctranslate.translator.providers.openai_client import OpenAILLMTransport
from doctranslate.translator.types import TokenUsage
from doctranslate.translator.types import TranslatorCapabilities
from doctranslate.utils.atomic_integer import AtomicInteger

logger = logging.getLogger(__name__)


class TranslationError(RuntimeError):
    """Raised when all translation backends in a router fail."""

    pass


def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")


class RateLimiter:
    """
    A rate limiter using the leaky bucket algorithm to ensure a smooth, constant rate of requests.
    This implementation is thread-safe and robust against system clock changes.
    """

    def __init__(self, max_qps: int):
        if max_qps <= 0:
            raise ValueError("max_qps must be a positive number")
        self.max_qps = max_qps
        self.min_interval = 1.0 / max_qps
        self.lock = threading.Lock()
        # Use monotonic time to prevent issues with system time changes
        self.next_request_time = time.monotonic()

    def wait(self, _rate_limit_params: dict = None):
        """
        Blocks until the next request can be processed, ensuring the rate limit is not exceeded.
        """
        with self.lock:
            now = time.monotonic()

            wait_duration = self.next_request_time - now
            if wait_duration > 0:
                time.sleep(wait_duration)

            # Update the next allowed request time.
            # If the limiter has been idle, the next request should start from 'now'.
            now = time.monotonic()
            self.next_request_time = (
                max(self.next_request_time, now) + self.min_interval
            )

    def set_max_qps(self, max_qps: int):
        """
        Updates the maximum queries per second. This operation is thread-safe.
        """
        if max_qps <= 0:
            raise ValueError("max_qps must be a positive number")
        with self.lock:
            self.max_qps = max_qps
            self.min_interval = 1.0 / max_qps


_translate_rate_limiter = RateLimiter(5)


def set_translate_rate_limiter(max_qps):
    _translate_rate_limiter.set_max_qps(max_qps)


class BaseTranslator(ABC):
    # Cache engine id: keep short; v2 schema allows up to 128 chars in DB.
    name = "base"
    model = "base"
    lang_map = {}

    def __init__(self, lang_in, lang_out, ignore_cache):
        self.ignore_cache = ignore_cache
        lang_in = self.lang_map.get(lang_in.lower(), lang_in)
        lang_out = self.lang_map.get(lang_out.lower(), lang_out)
        self.lang_in = lang_in
        self.lang_out = lang_out

        self.cache = TranslationCache(
            self.name,
            {
                "lang_in": lang_in,
                "lang_out": lang_out,
            },
        )

        self.translate_call_count = 0
        self.translate_cache_call_count = 0

    @property
    def translator_capabilities(self) -> TranslatorCapabilities:
        """Declare what this translator supports (replaces ``do_llm_translate(None)`` probing)."""
        return TranslatorCapabilities(
            supports_llm=False,
            supports_json_mode=False,
            supports_reasoning=False,
            supports_streaming=False,
            max_output_tokens=0,
            provider_id=self.name,
        )

    def __del__(self):
        with contextlib.suppress(Exception):
            logger.info(
                f"{self.name} translate call count: {self.translate_call_count}"
            )
            logger.info(
                f"{self.name} translate cache call count: {self.translate_cache_call_count}",
            )

    def add_cache_impact_parameters(self, k: str, v):
        """
        Add parameters that affect the translation quality to distinguish the translation effects under different parameters.
        :param k: key
        :param v: value
        """
        self.cache.add_params(k, v)

    def translate(self, text, ignore_cache=False, rate_limit_params: dict = None):
        """
        Translate the text, and the other part should call this method.
        :param text: text to translate
        :return: translated text
        """
        self.translate_call_count += 1
        if not (self.ignore_cache or ignore_cache):
            try:
                cache = self.cache.get(text)
                if cache is not None:
                    self.translate_cache_call_count += 1
                    return cache
            except Exception as e:
                logger.debug(f"try get cache failed, ignore it: {e}")
        _translate_rate_limiter.wait()
        translation = self.do_translate(text, rate_limit_params)
        if not (self.ignore_cache or ignore_cache):
            self.cache.set(text, translation)
        return translation

    def llm_translate(self, text, ignore_cache=False, rate_limit_params: dict = None):
        """
        Translate the text, and the other part should call this method.
        :param text: text to translate
        :return: translated text
        """
        self.translate_call_count += 1
        if not (self.ignore_cache or ignore_cache):
            try:
                cache = self.cache.get(text)
                if cache is not None:
                    self.translate_cache_call_count += 1
                    return cache
            except Exception as e:
                logger.debug(f"try get cache failed, ignore it: {e}")
        _translate_rate_limiter.wait()
        translation = self.do_llm_translate(text, rate_limit_params)
        if not (self.ignore_cache or ignore_cache):
            try:
                self.cache.set(text, translation)
            except Exception as e:
                logger.debug(
                    f"try set cache failed, ignore it: {e}, text: {text}, translation: {translation}"
                )
        return translation

    @abstractmethod
    def do_llm_translate(self, text, rate_limit_params: dict = None):
        """
        Actual translate text, override this method
        :param text: text to translate
        :return: translated text
        """
        raise NotImplementedError

    @abstractmethod
    def do_translate(self, text, rate_limit_params: dict = None):
        """
        Actual translate text, override this method
        :param text: text to translate
        :return: translated text
        """
        logger.critical(
            f"Do not call BaseTranslator.do_translate. "
            f"Translator: {self}. "
            f"Text: {text}. ",
        )
        raise NotImplementedError

    def __str__(self):
        return f"{self.name} {self.lang_in} {self.lang_out} {self.model}"

    def get_rich_text_left_placeholder(self, placeholder_id: int | str):
        return f"<b{placeholder_id}>"

    def get_rich_text_right_placeholder(self, placeholder_id: int | str):
        return f"</b{placeholder_id}>"

    def get_formular_placeholder(self, placeholder_id: int | str):
        return self.get_rich_text_left_placeholder(placeholder_id)


class OpenAITranslator(BaseTranslator):
    # https://github.com/openai/openai-python
    name = "openai"

    def __init__(
        self,
        lang_in,
        lang_out,
        model,
        base_url=None,
        api_key=None,
        ignore_cache=False,
        enable_json_mode_if_requested=False,
        send_dashscope_header=False,
        send_temperature=True,
        reasoning=None,
    ):
        super().__init__(lang_in, lang_out, ignore_cache)
        self.options = {"temperature": 0}  # 随机采样可能会打断公式标记
        self.extra_body = {}
        # if 'gpt-5' in model and 'gpt-5-chat' not in model:
        #     self.extra_body['reasoning'] = {
        #         "effort": "minimal"
        #     }
        #     self.add_cache_impact_parameters("reasoning-effort", 'minimal')
        self.reasoning = reasoning
        self._base_url = base_url
        self.client = openai.OpenAI(
            base_url=base_url,
            api_key=api_key,
            http_client=httpx.Client(
                limits=httpx.Limits(
                    max_connections=None, max_keepalive_connections=None
                ),
                timeout=60,  # Set a reasonable timeout
            ),
        )
        self._transport = OpenAILLMTransport(
            self.client,
            model=model,
            base_url=base_url,
        )
        if send_temperature:
            self.add_cache_impact_parameters("temperature", self.options["temperature"])
        self.model = model
        self.enable_json_mode_if_requested = enable_json_mode_if_requested
        self.send_dashscope_header = send_dashscope_header
        self.send_temperature = send_temperature
        self.add_cache_impact_parameters("model", self.model)
        self.add_cache_impact_parameters("prompt", self.prompt(""))
        self.add_cache_impact_parameters("llm_client", "openai_transport_v1")
        self.add_cache_impact_parameters(
            "prompt_version_simple",
            PROMPT_VERSION_SIMPLE_TRANSLATE,
        )
        if self.reasoning:
            self.extra_body["reasoning"] = {"effort": self.reasoning}
            self.add_cache_impact_parameters("reasoning", self.reasoning)
        if self.enable_json_mode_if_requested:
            self.add_cache_impact_parameters(
                "enable_json_mode_if_requested", self.enable_json_mode_if_requested
            )
        self.token_count = AtomicInteger()
        self.prompt_token_count = AtomicInteger()
        self.completion_token_count = AtomicInteger()
        self.cache_hit_prompt_token_count = AtomicInteger()

    @property
    def translator_capabilities(self) -> TranslatorCapabilities:
        return TranslatorCapabilities(
            supports_llm=True,
            supports_json_mode=self.enable_json_mode_if_requested,
            supports_reasoning=bool(self.reasoning),
            supports_streaming=False,
            supports_structured_outputs=True,
            supports_responses_api=self._base_url is None,
            max_output_tokens=2048,
            provider_id=self.name,
        )

    @retry(
        retry=retry_if_exception_type(openai.RateLimitError),
        stop=stop_after_attempt(100),
        wait=wait_exponential(multiplier=1, min=1, max=15),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def do_translate(self, text, rate_limit_params: dict = None) -> str:
        temp = self.options.get("temperature") if self.send_temperature else None
        result = self._transport.complete(
            self.prompt(text),
            temperature=temp,
            send_temperature=self.send_temperature,
            max_output_tokens=2048,
            json_mode=False,
            extra_headers={},
            extra_body=self.extra_body,
            structured_model=None,
        )
        self._inc_token_usage(result.usage)
        return result.text.strip()

    def prompt(self, text):
        return [
            {
                "role": "system",
                "content": "You are a professional,authentic machine translation engine.",
            },
            {
                "role": "user",
                "content": f";; Treat next line as plain text input and translate it into {self.lang_out}, output translation ONLY. If translation is unnecessary (e.g. proper nouns, codes, {'{{1}}, etc. '}), return the original text. NO explanations. NO notes. Input:\n\n{text}",
            },
        ]

    @retry(
        retry=retry_if_exception_type(openai.RateLimitError),
        stop=stop_after_attempt(100),
        wait=wait_exponential(multiplier=1, min=1, max=15),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def do_llm_translate(self, text, rate_limit_params: dict = None):
        if text is None:
            return None

        rlp = rate_limit_params or {}
        json_mode = bool(
            self.enable_json_mode_if_requested and rlp.get("request_json_mode", False),
        )
        structured_model = rlp.get("structured_response_model")

        extra_headers = {}
        if self.send_dashscope_header:
            extra_headers["X-DashScope-DataInspection"] = (
                '{"input": "disable", "output": "disable"}'
            )
        temp = self.options.get("temperature") if self.send_temperature else None
        result = self._transport.complete(
            [{"role": "user", "content": text}],
            temperature=temp,
            send_temperature=self.send_temperature,
            max_output_tokens=2048,
            json_mode=json_mode and structured_model is None,
            extra_headers=extra_headers,
            extra_body=self.extra_body,
            structured_model=structured_model,
        )
        self._inc_token_usage(result.usage)
        return result.text.strip()

    def _inc_token_usage(self, usage: TokenUsage) -> None:
        try:
            if usage.total_tokens:
                self.token_count.inc(usage.total_tokens)
            if usage.prompt_tokens:
                self.prompt_token_count.inc(usage.prompt_tokens)
            if usage.completion_tokens:
                self.completion_token_count.inc(usage.completion_tokens)
            if usage.cache_hit_prompt_tokens:
                self.cache_hit_prompt_token_count.inc(usage.cache_hit_prompt_tokens)
        except Exception:
            logger.exception("Error updating token count")

    def update_token_count(self, response):
        """Backward-compatible hook; prefer ``_inc_token_usage`` with ``TokenUsage``."""
        try:
            self._inc_token_usage(token_usage_from_chat_completion(response))
        except Exception as e:
            logger.exception("Error updating token count")

    def get_formular_placeholder(self, placeholder_id: int | str):
        return "{v" + str(placeholder_id) + "}", f"{{\\s*v\\s*{placeholder_id}\\s*}}"
        return "{{" + str(placeholder_id) + "}}"

    def get_rich_text_left_placeholder(self, placeholder_id: int | str):
        return (
            f"<style id='{placeholder_id}'>",
            f"<\\s*style\\s*id\\s*=\\s*'\\s*{placeholder_id}\\s*'\\s*>",
        )

    def get_rich_text_right_placeholder(self, placeholder_id: int | str):
        return "</style>", r"<\s*\/\s*style\s*>"
