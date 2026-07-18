"""OpenAI API backend for GPT and reasoning models.

Reasoning models (o-series and GPT-5 family) use max_completion_tokens
instead of max_tokens, don't accept temperature/top_p/seed parameters,
and hide their reasoning trace internally — it is NOT returned in the
response.

Reasoning-token budget note:
    For reasoning models, max_completion_tokens is a HARD CAP on the sum
    of internal reasoning tokens (billed but invisible) + visible output
    tokens. If reasoning consumes the entire budget, the API returns HTTP
    200 with finish_reason="length" and an empty content field.

    To prevent truncation, this backend adds a fixed reasoning buffer to
    the caller's requested max_new_tokens when constructing the API cap:
        max_completion_tokens = max_new_tokens + REASONING_TOKEN_BUFFER

    The buffer is a ceiling, not a floor — tokens are only billed when
    actually consumed. On items where reasoning is minimal, cost is close
    to what a smaller cap would have produced. The buffer only kicks in
    for items where the model reasons at length.

    IMPORTANT consequence for cross-model comparison: because reasoning and
    visible output share one pool and OpenAI does not expose the split, a
    reasoning model given a large combined budget can spend most of it on a
    long VISIBLE answer. This is why GPT-5's observed response lengths in
    this study far exceed backends whose reasoning is separately accounted
    (DeepSeek, Together/Qwen). finish_reason is captured so this is
    detectable rather than inferred from response length.

Older non-reasoning models (GPT-4 family) accept temperature and seed
for deterministic generation; these are applied inside generate() because
they are model-capability-dependent, not caller-supplied.

Requires: OPENAI_API_KEY environment variable.
"""

from __future__ import annotations

import os

import openai

from lbe.models.api_utils import DEFAULT_TIMEOUT, retry_with_backoff
from lbe.models.base import GenerationOutput, Model

# Prefix match: any model name starting with one of these uses the
# reasoning-model API (max_completion_tokens, no temperature, reasoning_effort).
# Covers o1, o3, o4, and the GPT-5 family (gpt-5, gpt-5-mini, gpt-5.1, etc.).
REASONING_MODEL_PREFIXES = ("o1", "o3", "o4", "gpt-5")

# Buffer added to max_completion_tokens for reasoning models.
# Reasoning tokens are billed against the same budget as visible output
# but are not returned in the response. A buffer of 8000 empirically
# accommodates medium-effort reasoning on most items; hard ethical or
# multi-step reasoning items may still hit the ceiling.
REASONING_TOKEN_BUFFER = 8000


class OpenAIBackend(Model):
    """Backend for OpenAI models via API.

    Attributes:
        model_name: OpenAI model identifier (e.g., "gpt-5", "o4-mini").
        timeout: Per-request timeout in seconds.
        is_reasoning: Whether this model uses the reasoning-model API.
    """

    def __init__(
        self,
        model_name: str,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the backend.

        Args:
            model_name: OpenAI model identifier.
            api_key: API key. If None, read from OPENAI_API_KEY env var.
            timeout: Per-request timeout in seconds.
        """
        self.model_name = model_name
        self.timeout = timeout
        self.is_reasoning = model_name.startswith(REASONING_MODEL_PREFIXES)

        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError(
                "OPENAI_API_KEY not set. Add it to your environment " "or pass api_key= explicitly."
            )
        self.client = openai.OpenAI(api_key=key, timeout=timeout)

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 500,
    ) -> GenerationOutput:
        """Generate a response.

        For reasoning models (o-series and GPT-5 family), internal reasoning
        is not returned; only the final answer is available. A fixed reasoning
        buffer is added to max_new_tokens to prevent the model from exhausting
        the token budget on internal reasoning before producing visible output.

        Args:
            prompt: User prompt.
            max_new_tokens: Max tokens for the visible answer. For reasoning
                models, an internal reasoning buffer is added on top when
                constructing the API cap; the caller does not need to account
                for reasoning tokens.

        Returns:
            GenerationOutput. `finish_reason` is OpenAI's verbatim value;
            "length" means the combined reasoning+visible budget ran out,
            which GenerationOutput.truncated normalizes to True. Note that
            for reasoning models a "length" finish can mean either "the
            answer was cut off" or "reasoning ate the whole budget and no
            answer was produced" — check whether text is empty to
            distinguish.
        """

        def _call():
            kwargs: dict = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
            }
            if self.is_reasoning:
                # Reasoning models: max_completion_tokens covers reasoning +
                # visible output. Add buffer so reasoning doesn't starve the
                # visible answer. Temperature/seed rejected by these models.
                kwargs["max_completion_tokens"] = max_new_tokens + REASONING_TOKEN_BUFFER
                kwargs["reasoning_effort"] = "medium"
            else:
                # Non-reasoning models (GPT-4 family): standard controls.
                kwargs["max_tokens"] = max_new_tokens
                kwargs["temperature"] = 0.0
                kwargs["seed"] = 42
            return self.client.chat.completions.create(**kwargs)

        response = retry_with_backoff(_call)
        choice = response.choices[0]

        return GenerationOutput(
            text=choice.message.content or "",
            prompt=prompt,
            model_name=self.model_name,
            finish_reason=getattr(choice, "finish_reason", None),
            # OpenAI reasoning models do not expose the trace at all.
            reasoning_text=None,
        )
