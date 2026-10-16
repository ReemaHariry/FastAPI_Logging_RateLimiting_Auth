import logging

from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAILLMClient:
    """OpenAI client wrapper built once and reused across requests."""

    def __init__(self, api_key: str, base_url: str | None = None) -> None:
        if base_url:
            self.client = OpenAI(base_url=base_url, api_key=api_key)
        else:
            self.client = OpenAI(api_key=api_key)

    def chat(
        self,
        text: str,
        model: str,
        temperature: float,
        system_prompt: str | None = None,
    ) -> str:

        messages: list[dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": text})

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=300,
            )
            content = response.choices[0].message.content or ""
            logger.info(f"LLM ok | model={model} | out_len={len(content)}")
            return content
        except Exception as e:
            logger.error(f"LLM call failed | model={model} | error={e}")
            raise
