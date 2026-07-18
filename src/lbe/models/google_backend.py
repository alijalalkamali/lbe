"""Google Gemini API backend.

Uses the OpenAI-compatible endpoint that Google provides for Gemini models,
called via the standard openai Python SDK with a Gemini-specific base_url.

Verified against Google's June 2026 documentation:
https://ai.google.dev/gemini-api/docs/openai

Model naming (as of June 2026):
    - gemini-2.5-pro       : previous stable flagship (recommended for
                             reproducibility in research)
    - gemini-2.5-flash     : lightweight, fast, stable
    - gemini-3.1-pro-preview: latest preview flagship (higher capability,
                              lower daily quota, subject to deprecation)
    - gemini-3.5-flash     : current-generation lightweight

Reasoning-token budget note:
    Gemini reasoning-capable models (2.5-pro, 3.x-pro-preview) burn internal
    reasoning tokens against the same max_tokens budget as visible output,
    same mechanism as GPT-5. Without a reasoning buffer, the visible output
    is truncated at 15-25 tokens on judgment-heavy prompts because reasoning
    consumes the entire budget.

    To prevent truncation, this backend adds a fixed reasoning buffer to
    the caller's requested max_new_tokens for models that use extended
    reasoning. The buffer is a CEILING, not a floor — tokens are only
    billed when actually consumed.

Parameter support note:
    Google's OpenAI-compat layer rejects the `seed` parameter (returns 400).
    This backend omits seed. Outputs at temperature=0.0 are close-to-
    deterministic but not identically reproducible across runs like
    seed-supporting backends.

Requires: GEMINI_API_KEY or GOOGLE_API_KEY environment variable.
If both are set, GOOGLE_API_KEY takes precedence (Google's convention).
"""

from __future__ import annotations

import os

import openai

from lbe.models.api_utils import DEFAULT_TIMEOUT, retry_with_backoff
from lbe.models.base import GenerationOutput, Model

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

# Buffer added to max_tokens for Gemini models that use extended reasoning.
# Same mechanism as OpenAI reasoning models: internal reasoning tokens
# are billed against the same budget as visible output. Buffer is a
# ceiling — only billed when consumed.
REASONING_TOKEN_BUFFER = 4000

# Substring match: any model name containing any of these fragments is
# treated as reasoning-capable and gets the reasoning buffer added.
# Covers 2.5-pro, 3-pro-preview, 3.1-pro-preview, and future *-pro-* releases.
REASONING_MODEL_SUBSTRINGS = ("-pro",)


def _get_api_key() -> str | None:
    """Read the Gemini API key from the environment.

    GOOGLE_API_KEY takes precedence over GEMINI_API_KEY, matching Google's
    documented convention.
    """
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")


class GoogleBackend(Model):
    """Backend for Google Gemini models via the OpenAI-compat endpoint.

    Attributes:
        model_name: Gemini model identifier (e.g., "gemini-2.5-pro").
        timeout: Per-request timeout in seconds.
        is_reasoning: Whether this model uses extended reasoning against the
            visible token budget and therefore needs a buffer.
    """

    def __init__(
        self,
        model_name: str,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the backend.

        Args:
            model_name: Gemini model identifier.
            api_key: API key. If None, read from GOOGLE_API_KEY or
                GEMINI_API_KEY env var.
            timeout: Per-request timeout in seconds.
        """
        self.model_name = model_name
        self.timeout = timeout
        self.is_reasoning = any(fragment in model_name for fragment in REASONING_MODEL_SUBSTRINGS)

        key = api_key or _get_api_key()
        if not key:
            raise RuntimeError(
                "Neither GOOGLE_API_KEY nor GEMINI_API_KEY is set. "
                "Add one to your environment or pass api_key= explicitly."
            )
        self.client = openai.OpenAI(
            api_key=key,
            base_url=GEMINI_BASE_URL,
            timeout=timeout,
        )

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 500,
    ) -> GenerationOutput:
        """Generate a response from Gemini.

        For reasoning-capable pro-tier models, adds a reasoning buffer
        to max_tokens to prevent the model from exhausting the token
        budget on internal reasoning before producing visible output.

        Args:
            prompt: User prompt.
            max_new_tokens: Max tokens for the visible answer. For
                reasoning-capable models, an internal reasoning buffer
                is added on top when constructing the API cap.

        Returns:
            GenerationOutput. `finish_reason` is the compat layer's
            verbatim value; "length" normalizes to truncated=True.
        """

        def _call():
            # Add reasoning buffer for pro-tier models. Flash-tier models
            # don't use extended reasoning against the visible budget.
            effective_max_tokens = (
                max_new_tokens + REASONING_TOKEN_BUFFER if self.is_reasoning else max_new_tokens
            )
            return self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=effective_max_tokens,
                temperature=0.0,
            )

        response = retry_with_backoff(_call)
        choice = response.choices[0]

        return GenerationOutput(
            text=choice.message.content or "",
            prompt=prompt,
            model_name=self.model_name,
            finish_reason=getattr(choice, "finish_reason", None),
            # Gemini's OpenAI-compat layer does not surface the reasoning
            # trace separately.
            reasoning_text=None,
        )
