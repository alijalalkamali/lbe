"""Anthropic API backend for Claude models.

Supports adaptive extended thinking on Opus 4.6+, Sonnet 4.6+, and 5.x
models via the current API (thinking.type: "adaptive" + output_config.effort).
The older thinking.type: "enabled" + budget_tokens API is not used because
it was removed on Opus 4.7 and later.

Response format:
    - Without thinking: returns just the answer text
    - With thinking: returns "<thinking>...</thinking>\\n\\n<answer>"

Model handling:
    - Haiku 4.5: no extended thinking (not supported by model)
    - Sonnet 4.6, Opus 4.6: adaptive thinking; temperature parameter accepted
    - Opus 4.7, Opus 4.8, Sonnet 5, and newer: adaptive thinking; temperature
      rejected by the API and omitted from requests

Sampling controls:
    Set at construction time, not per generate() call — see base.py's module
    docstring. For models in NO_SAMPLING_PARAM_MODELS the API rejects
    temperature/top_p/top_k outright, so requests omit them entirely and
    generation is NOT deterministic across runs. This is a provider
    constraint, not a design choice.

Requires: ANTHROPIC_API_KEY environment variable.
"""

from __future__ import annotations

import os

import anthropic

from lbe.models.api_utils import DEFAULT_TIMEOUT, retry_with_backoff
from lbe.models.base import GenerationOutput, Model

# Buffer added to max_tokens to give adaptive thinking room to reason.
# max_tokens is a hard cap on thinking + response combined.
THINKING_TOKEN_BUFFER = 4000

# Effort level for adaptive thinking. Options: low, medium, high, xhigh, max.
# "high" is the API default and produces useful reasoning for most items.
DEFAULT_EFFORT = "high"

# Models that support the current adaptive thinking API.
ADAPTIVE_THINKING_MODELS: set[str] = {
    "claude-opus-4-6",
    "claude-opus-4-7",
    "claude-opus-4-8",
    "claude-sonnet-4-6",
    "claude-sonnet-5",
    "claude-fable-5",
    "claude-mythos-5",
    "claude-mythos-preview",
}

# Models that reject temperature / top_p / top_k parameters.
# Requests to these models omit sampling controls entirely.
NO_SAMPLING_PARAM_MODELS: set[str] = {
    "claude-opus-4-7",
    "claude-opus-4-8",
    "claude-sonnet-5",
    "claude-fable-5",
    "claude-mythos-5",
    "claude-mythos-preview",
}


class AnthropicBackend(Model):
    """Backend for Anthropic Claude models via API.

    Attributes:
        model_name: Anthropic model identifier (e.g., "claude-opus-4-7").
        timeout: Per-request timeout in seconds.
        enable_thinking: Whether adaptive thinking is used for this instance.
            Automatically disabled for models that don't support it.
    """

    def __init__(
        self,
        model_name: str,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        enable_thinking: bool = True,
    ) -> None:
        """Initialize the backend.

        Args:
            model_name: Claude model identifier.
            api_key: API key. If None, read from ANTHROPIC_API_KEY env var.
            timeout: Per-request timeout in seconds.
            enable_thinking: If True and the model supports adaptive thinking,
                enable it. Silently ignored for models without support (e.g.
                Haiku).
        """
        self.model_name = model_name
        self.timeout = timeout
        self.enable_thinking = enable_thinking and model_name in ADAPTIVE_THINKING_MODELS
        self._accepts_sampling_params = model_name not in NO_SAMPLING_PARAM_MODELS

        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Add it to your environment "
                "or pass api_key= explicitly."
            )
        self.client = anthropic.Anthropic(api_key=key, timeout=timeout)

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 500,
    ) -> GenerationOutput:
        """Generate a response from Claude.

        When adaptive thinking is enabled, the thinking summary is prepended
        to the response wrapped in <thinking>...</thinking> tags, followed
        by the final answer. Thinking is billed for the full generated
        tokens even though the returned content is summarized.

        Args:
            prompt: User prompt.
            max_new_tokens: Max tokens for the answer portion. A thinking
                buffer is added to the API's max_tokens cap so reasoning
                has room to complete.

        Returns:
            GenerationOutput. `finish_reason` carries Anthropic's
            stop_reason verbatim; "max_tokens" there means the combined
            thinking+answer budget was exhausted mid-generation, which
            GenerationOutput.truncated normalizes to True.
        """

        def _call():
            kwargs: dict = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
            }
            if self.enable_thinking:
                # Adaptive thinking: model decides depth based on complexity.
                # display="summarized" needed because 4.7+ default to "omitted"
                # which returns thinking blocks with empty content.
                kwargs["max_tokens"] = max_new_tokens + THINKING_TOKEN_BUFFER
                kwargs["thinking"] = {
                    "type": "adaptive",
                    "display": "summarized",
                }
                kwargs["output_config"] = {"effort": DEFAULT_EFFORT}
                # Do not set temperature: newer models reject it, and older
                # models with adaptive thinking do not require it.
            else:
                kwargs["max_tokens"] = max_new_tokens
                if self._accepts_sampling_params:
                    kwargs["temperature"] = 0.0
            return self.client.messages.create(**kwargs)

        response = retry_with_backoff(_call)

        # Parse content blocks: separate thinking from final answer.
        thinking_text = ""
        answer_text = ""
        for block in response.content:
            if block.type == "thinking":
                thinking_text = block.thinking
            elif block.type == "redacted_thinking":
                thinking_text = "[redacted by safety filter]"
            elif block.type == "text":
                answer_text = block.text

        if thinking_text:
            text = f"<thinking>\n{thinking_text}\n</thinking>\n\n{answer_text}"
        else:
            text = answer_text

        return GenerationOutput(
            text=text,
            prompt=prompt,
            model_name=self.model_name,
            finish_reason=getattr(response, "stop_reason", None),
            reasoning_text=thinking_text or None,
        )
