"""Together AI backend for models hosted on Together's inference platform.

Hosts both open-weight models (Llama, Gemma, DeepSeek variants) and
closed-weight models proxied as a third-party API pass-through
(e.g. Qwen3.7-Max, which has no public weight release). Do not infer weight
availability from the fact that a model is served here.

Streaming: this backend always uses streaming API calls. Some newer
Together-hosted models (e.g., Qwen3.7-Max) require stream=True and reject
non-streaming requests with a 400 error. Streaming works on all models
that support non-streaming, so always-streaming is a strict superset.

The caller of generate() sees no difference — the backend accumulates
streamed chunks into a single GenerationOutput before returning.

Reasoning-capable models (e.g., Qwen3.7-Max) return their reasoning trace
in a separate `reasoning` field on each streamed delta, distinct from
`content`. This backend captures both and returns them concatenated with
<thinking>...</thinking> delimiters, matching the format used by the
Anthropic and DeepSeek backends. Reasoning tokens count against the
model's max_tokens budget, so a fixed buffer is added on top of the
caller's requested max_new_tokens for reasoning models, preventing the
model from exhausting its budget on reasoning before producing any
visible answer.

Models NOT in REASONING_MODELS get no buffer at all — their entire budget
is max_new_tokens. This is correct (they have no reasoning trace to fund)
but means their effective visible-answer ceiling is materially lower than
backends where reasoning and answer share an inflated pool. finish_reason
is captured so truncation is detectable rather than inferred.

Model identifiers use the upstream form (e.g., "meta-llama/Llama-3.3-70B-
Instruct-Turbo"); the "together:" routing prefix is stripped by the factory
before this backend is instantiated.

Requires: TOGETHER_API_KEY environment variable.
"""

from __future__ import annotations

import os

import together

from lbe.models.api_utils import DEFAULT_TIMEOUT, retry_with_backoff
from lbe.models.base import GenerationOutput, Model

REASONING_TOKEN_BUFFER = 4000
REASONING_MODELS = {"Qwen/Qwen3.7-Max"}


class TogetherBackend(Model):
    """Backend for models hosted on Together AI.

    Attributes:
        model_name: Together model identifier.
        timeout: Per-request timeout in seconds.
        is_reasoning: Whether this model returns a reasoning trace and
            needs a token-budget buffer to avoid truncating the answer.
    """

    def __init__(
        self,
        model_name: str,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the backend.

        Args:
            model_name: Model identifier (upstream form, no "together:" prefix).
            api_key: API key. If None, read from TOGETHER_API_KEY env var.
            timeout: Per-request timeout in seconds.
        """
        self.model_name = model_name
        self.timeout = timeout
        self.is_reasoning = model_name in REASONING_MODELS

        key = api_key or os.environ.get("TOGETHER_API_KEY")
        if not key:
            raise RuntimeError(
                "TOGETHER_API_KEY not set. Add it to your environment "
                "or pass api_key= explicitly."
            )
        self.client = together.Together(api_key=key, timeout=timeout)

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 500,
    ) -> GenerationOutput:
        """Generate a response via streaming.

        Uses the streaming API and accumulates chunks into a single output.
        This is required for models like Qwen3.7-Max that reject non-streaming
        requests, and works transparently for models that support both modes.

        For reasoning models, the reasoning trace (returned in each delta's
        `reasoning` field) is captured separately from `content` and
        prepended to the final answer wrapped in <thinking>...</thinking>
        tags. A token buffer is added to max_new_tokens for these models so
        that reasoning has room to complete before the visible answer
        needs to be produced.

        Args:
            prompt: User prompt.
            max_new_tokens: Max tokens for the visible answer. For
                reasoning models, an internal reasoning buffer is added on
                top when constructing the API cap; the caller does not
                need to account for reasoning tokens.

        Returns:
            GenerationOutput. `finish_reason` is read from the final stream
            chunk that carries one — in the streaming API the reason arrives
            on a trailing chunk whose delta is typically empty, so it must
            be captured during iteration rather than read off a response
            object afterwards.
        """

        def _call() -> GenerationOutput:
            effective_max_tokens = (
                max_new_tokens + REASONING_TOKEN_BUFFER if self.is_reasoning else max_new_tokens
            )
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=effective_max_tokens,
                temperature=0.0,
                seed=42,
                stream=True,
            )
            # Accumulate streamed chunks into a single response.
            # Each chunk carries a partial delta; concatenating deltas
            # reconstructs the complete response. Reasoning-capable models
            # stream their reasoning trace via a separate `reasoning` field
            # on the delta, distinct from `content`.
            parts: list[str] = []
            reasoning_parts: list[str] = []
            finish_reason: str | None = None
            for chunk in stream:
                if not chunk.choices:
                    continue
                choice = chunk.choices[0]
                # The terminal chunk carries finish_reason with an empty
                # delta. Keep the last non-None value seen rather than
                # breaking, so the stream is always fully drained.
                chunk_finish = getattr(choice, "finish_reason", None)
                if chunk_finish:
                    finish_reason = chunk_finish
                delta = choice.delta
                if delta.content:
                    parts.append(delta.content)
                reasoning_text = getattr(delta, "reasoning", None)
                if reasoning_text:
                    reasoning_parts.append(reasoning_text)

            answer = "".join(parts)
            reasoning = "".join(reasoning_parts)
            text = f"<thinking>\n{reasoning}\n</thinking>\n\n{answer}" if reasoning else answer
            return GenerationOutput(
                text=text,
                prompt=prompt,
                model_name=self.model_name,
                finish_reason=finish_reason,
                reasoning_text=reasoning or None,
            )

        return retry_with_backoff(_call)
