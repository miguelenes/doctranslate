"""OpenAI SDK transport: Responses API first (default host), chat completions fallback."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import openai

from doctranslate.translator.llm.usage import token_usage_from_chat_completion
from doctranslate.translator.llm.usage import token_usage_from_openai_response
from doctranslate.translator.types import CompletionResult
from doctranslate.translator.types import LLMTransportKind

logger = logging.getLogger(__name__)

_DASHSCOPE_FILTER = (
    "系统检测到输入或生成内容可能包含不安全或敏感内容，请您避免输入易产生敏感内容的提示语，感谢您的配合。"
)


def _messages_to_instructions_and_input(
    messages: list[dict[str, str]],
) -> tuple[str | None, str]:
    """Split chat messages into Responses API ``instructions`` + ``input``."""
    system_parts: list[str] = []
    other_parts: list[str] = []
    for m in messages:
        role = m.get("role", "")
        content = (m.get("content") or "").strip()
        if not content:
            continue
        if role == "system":
            system_parts.append(content)
        else:
            other_parts.append(content)
    instructions = "\n\n".join(system_parts) if system_parts else None
    user_input = "\n\n".join(other_parts) if other_parts else ""
    return instructions, user_input


def _should_try_responses_api(base_url: str | None) -> bool:
    """Use Responses API only for default OpenAI endpoint (no custom gateway)."""
    return base_url is None or str(base_url).strip() == ""


class OpenAILLMTransport:
    """Single place for OpenAI chat vs Responses vs parse completions."""

    def __init__(
        self,
        client: openai.OpenAI,
        *,
        model: str,
        base_url: str | None,
    ):
        self._client = client
        self._model = model
        self._base_url = base_url

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float | None,
        send_temperature: bool,
        max_output_tokens: int,
        json_mode: bool,
        extra_headers: dict[str, str],
        extra_body: dict[str, Any],
        structured_model: type[Any] | None = None,
    ) -> CompletionResult:
        """Run a completion; prefers structured parse, then Responses (text), then chat."""
        t0 = time.perf_counter()
        if structured_model is not None:
            return self._complete_parse(
                messages,
                temperature=temperature,
                send_temperature=send_temperature,
                max_output_tokens=max_output_tokens,
                extra_headers=extra_headers,
                extra_body=extra_body,
                structured_model=structured_model,
                t0=t0,
            )

        use_responses = _should_try_responses_api(self._base_url) and not json_mode
        if use_responses:
            try:
                return self._complete_responses(
                    messages,
                    temperature=temperature,
                    send_temperature=send_temperature,
                    max_output_tokens=max_output_tokens,
                    extra_headers=extra_headers,
                    extra_body=extra_body,
                    t0=t0,
                )
            except Exception as e:
                logger.debug("Responses API failed, falling back to chat.completions: %s", e)

        return self._complete_chat(
            messages,
            temperature=temperature,
            send_temperature=send_temperature,
            max_output_tokens=max_output_tokens,
            json_mode=json_mode,
            extra_headers=extra_headers,
            extra_body=extra_body,
            t0=t0,
        )

    def _complete_parse(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float | None,
        send_temperature: bool,
        max_output_tokens: int,
        extra_headers: dict[str, str],
        extra_body: dict[str, Any],
        structured_model: type[Any],
        t0: float,
    ) -> CompletionResult:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "response_format": structured_model,
            "max_tokens": max_output_tokens,
            "extra_headers": extra_headers or None,
            "extra_body": extra_body or None,
        }
        if send_temperature and temperature is not None:
            kwargs["temperature"] = temperature
        try:
            response = self._client.chat.completions.parse(**kwargs)
        except openai.BadRequestError as e:
            if _DASHSCOPE_FILTER in str(e):
                from doctranslate.babeldoc_exception.BabelDOCException import (
                    ContentFilterError,
                )

                raise ContentFilterError(str(e)) from e
            raise
        latency_ms = (time.perf_counter() - t0) * 1000.0
        usage = token_usage_from_chat_completion(response)
        msg = response.choices[0].message
        parsed = getattr(msg, "parsed", None)
        refusal = getattr(msg, "refusal", None)
        text = (msg.content or "").strip() if msg is not None else ""
        if parsed is not None:
            text = json.dumps(parsed.model_dump(), ensure_ascii=False)
        return CompletionResult(
            text=text,
            usage=usage,
            latency_ms=latency_ms,
            raw_response=response,
            parsed=parsed,
            refusal=refusal,
            transport=LLMTransportKind.OPENAI_CHAT_COMPLETIONS,
        )

    def _complete_responses(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float | None,
        send_temperature: bool,
        max_output_tokens: int,
        extra_headers: dict[str, str],
        extra_body: dict[str, Any],
        t0: float,
    ) -> CompletionResult:
        instructions, user_input = _messages_to_instructions_and_input(messages)
        kwargs: dict[str, Any] = {
            "model": self._model,
            "input": user_input,
            "max_output_tokens": max_output_tokens,
            "extra_headers": extra_headers or None,
            "extra_body": extra_body or None,
        }
        if instructions:
            kwargs["instructions"] = instructions
        if send_temperature and temperature is not None:
            kwargs["temperature"] = temperature
        try:
            response = self._client.responses.create(**kwargs)
        except openai.BadRequestError as e:
            if _DASHSCOPE_FILTER in str(e):
                from doctranslate.babeldoc_exception.BabelDOCException import (
                    ContentFilterError,
                )

                raise ContentFilterError(str(e)) from e
            raise
        latency_ms = (time.perf_counter() - t0) * 1000.0
        usage = token_usage_from_openai_response(response)
        text = (getattr(response, "output_text", None) or "").strip()
        if not text:
            raise RuntimeError("Empty Responses API output_text")
        return CompletionResult(
            text=text,
            usage=usage,
            latency_ms=latency_ms,
            raw_response=response,
            transport=LLMTransportKind.OPENAI_RESPONSES,
        )

    def _complete_chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float | None,
        send_temperature: bool,
        max_output_tokens: int,
        json_mode: bool,
        extra_headers: dict[str, str],
        extra_body: dict[str, Any],
        t0: float,
    ) -> CompletionResult:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "max_tokens": max_output_tokens,
            "extra_headers": extra_headers or None,
            "extra_body": extra_body or None,
        }
        if send_temperature and temperature is not None:
            kwargs["temperature"] = temperature
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        try:
            response = self._client.chat.completions.create(**kwargs)
        except openai.BadRequestError as e:
            if _DASHSCOPE_FILTER in str(e):
                from doctranslate.babeldoc_exception.BabelDOCException import (
                    ContentFilterError,
                )

                raise ContentFilterError(str(e)) from e
            raise
        latency_ms = (time.perf_counter() - t0) * 1000.0
        usage = token_usage_from_chat_completion(response)
        msg = response.choices[0].message
        text = (msg.content or "").strip() if msg is not None else ""
        return CompletionResult(
            text=text,
            usage=usage,
            latency_ms=latency_ms,
            raw_response=response,
            transport=LLMTransportKind.OPENAI_CHAT_COMPLETIONS,
        )
