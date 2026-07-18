"""DeepSeek API backend.

Uses the OpenAI Python SDK (openai package) pointed at DeepSeek's endpoint.
Same SDK, different base_url and API key.

For deepseek-reasoner (R1), the reasoning trace is returned in a separate
reasoning_content field on the message, distinct from the final content.
This backend captures both and returns them concatenated with <thinking>
delimiters, matching the format of the Anthropic backend for consistency.

Because reasoning arrives in its own field rather than sharing the visible
output stream, the visible answer here is NOT inflated by reasoning the way
it is for OpenAI reasoning models — a difference that matters when
comparing response lengths across backends.

Sampling controls:
    deepseek-reasoner does not accept a temperature parameter; requests omit
    it and generation is not deterministic across runs. deepseek-chat (V3)
    does accept it. This is a provider constraint, not a design choice.

Requires: DEEPSEEK_API_KEY environment variable.
"""

from __future__ import annotations

import os

import openai

from lbe.models.api_utils import DEFAULT_TIMEOUT, retry_with_backoff
from lbe.models.base import GenerationOutput, Model

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
REASONING_TOKEN_BUFFER = 4000
REASONING_MODELS = {"deepseek-reasoner"}


class DeepSeekBackend(Model):
    """Backend for DeepSeek models via API (OpenAI-compatible interface).

    Attributes:
        model_name: DeepSeek model identifier.
        timeout: Per-request timeout in seconds.
        is_reasoning: Whether this is the deepseek-reasoner model.
    """

    def __init__(
        self,
        model_name: str,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the backend.

        Args:
            model_name: DeepSeek model identifier.
            api_key: API key. If None, read from DEEPSEEK_API_KEY env var.
            timeout: Per-request timeout in seconds.
        """
        self.model_name = model_name
        self.timeout = timeout
        self.is_reasoning = model_name in REASONING_MODELS

        key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not key:
            raise RuntimeError(
                "DEEPSEEK_API_KEY not set. Add it to your environment "
                "or pass api_key= explicitly."
            )
        self.client = openai.OpenAI(
            api_key=key,
            base_url=DEEPSEEK_BASE_URL,
            timeout=timeout,
        )

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 500,
    ) -> GenerationOutput:
        """Generate a response.

        For deepseek-reasoner, reasoning is prepended in <thinking>...</thinking>
        tags followed by the final answer.

        Args:
            prompt: User prompt.
            max_new_tokens: Max tokens in the response (excludes reasoning trace
                for reasoner model — reasoning has its own implicit budget).

        Returns:
            GenerationOutput. `finish_reason` is DeepSeek's verbatim value;
            "length" normalizes to truncated=True.
        """

        def _call():
            effective_max_tokens = (
                max_new_tokens + REASONING_TOKEN_BUFFER if self.is_reasoning else max_new_tokens
            )
            kwargs: dict = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": effective_max_tokens,
            }
            return self.client.chat.completions.create(**kwargs)

        response = retry_with_backoff(_call)
        choice = response.choices[0]
        message = choice.message
        answer = message.content or ""

        # deepseek-reasoner returns reasoning in a distinct field
        reasoning = getattr(message, "reasoning_content", None)
        if reasoning:
            text = f"<thinking>\n{reasoning}\n</thinking>\n\n{answer}"
        else:
            text = answer

        return GenerationOutput(
            text=text,
            prompt=prompt,
            model_name=self.model_name,
            finish_reason=getattr(choice, "finish_reason", None),
            reasoning_text=reasoning or None,
        )
