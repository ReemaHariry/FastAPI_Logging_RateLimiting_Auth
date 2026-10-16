"""Deterministic OpenAI-compatible client used for offline development.

This client mimics `OpenAILLMClient.chat()` without performing any network
calls, so the app can run end-to-end (including `/summarize`, `/generate`)
without an API key or a running model.

Enable it by setting `OPENAI_BASE_URL=fake` in your `.env` file.
"""

import logging

logger = logging.getLogger(__name__)


class FakeLLMClient:
    """Drop-in replacement for OpenAILLMClient with zero network calls."""

    def __init__(self) -> None:  # accept and ignore real-client args
        pass

    def chat(
        self,
        text: str,
        model: str,
        temperature: float,
        system_prompt: str | None = None,
    ) -> str:
        prefix = f"[fake:{model}]"
        if system_prompt:
            short_prompt = system_prompt.strip().splitlines()[0][:60]
            result = f"{prefix} {short_prompt} -> {text[:120]}"
        else:
            result = f"{prefix} {text[:120]}"
        logger.info(f"Fake LLM ok | model={model} | out_len={len(result)}")
        return result
