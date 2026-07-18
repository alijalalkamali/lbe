"""Base classes and types for the model abstraction layer.

Every model backend (local HuggingFace models, Anthropic API, etc.) implements
the Model interface defined here. Eval code calls model.generate(prompt) and
gets back a GenerationOutput, regardless of which backend produced it.

Interface scope note:
    generate() intentionally declares only `prompt` and `max_new_tokens` —
    the two parameters every backend can actually honor. Sampling controls
    (temperature, seed, reasoning effort) are deliberately NOT part of the
    interface: three of the six provider APIs used in this project reject
    them outright for reasoning models (OpenAI GPT-5 family, DeepSeek
    R1, Anthropic Opus 4.7+). An abstract method that declares parameters
    most implementers must silently ignore is a broken contract — callers
    pass them, assume they took effect, and get non-reproducible results
    with no error. Backends that DO support sampling controls accept them
    at construction time and document exactly what they apply.

    Subclasses MAY accept additional optional keyword arguments beyond the
    declared signature (LocalHFModel does, for temperature/seed). This
    remains substitutable for any caller using only the declared interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

# Provider-specific finish/stop-reason strings meaning "the response was cut
# off at the token ceiling" rather than "the model finished what it wanted to
# say". Normalized here so downstream code never needs a provider lookup
# table to answer "was this truncated?".
#
#   "length"     — OpenAI, DeepSeek, Together, Google's OpenAI-compat layer
#   "max_tokens" — Anthropic
TRUNCATION_FINISH_REASONS: frozenset[str] = frozenset({"length", "max_tokens"})


@dataclass
class GenerationOutput:
    """Structured output from a single model generation call.

    Attributes:
        text: The response text. For backends that expose a reasoning trace
            (Anthropic, DeepSeek, Together/Qwen), this includes the trace
            wrapped in <thinking>...</thinking> followed by the answer,
            matching the format written to the results files.
        prompt: The prompt that produced this output.
        model_name: Identifier of the model that generated it.
        finish_reason: The provider's raw stop-reason string, verbatim and
            un-normalized (e.g. "stop", "length", "end_turn", "max_tokens").
            None for backends that don't report one. Kept raw rather than
            normalized so the original provider signal is auditable; use
            `truncated` for the normalized question.
        reasoning_text: The raw reasoning trace, where the provider exposes
            it separately. None otherwise. Stored separately from `text` so
            downstream analysis can distinguish "the model reasoned at
            length" from "the model wrote a long answer" — these have very
            different implications for token-budget accounting.
        logprobs: Only populated by local backends with return_logprobs=True.
        hidden_states: Only populated by local backends with
            return_hidden_states=True. Relevant to the mechanistic-
            interpretability phase, not the behavioral study.

    Note:
        API backends leave logprobs/hidden_states as None.
    """

    text: str
    prompt: str
    model_name: str
    finish_reason: str | None = None
    reasoning_text: str | None = None
    logprobs: list[float] | None = field(default=None)
    hidden_states: list | None = field(default=None)

    @property
    def truncated(self) -> bool:
        """True if generation stopped because it hit the token ceiling.

        Derived from finish_reason rather than stored, so it can never fall
        out of sync with the provider's reported reason. Returns False when
        finish_reason is None (backend doesn't report one) — absence of a
        signal is not evidence of truncation, and callers who need to
        distinguish "known complete" from "unknown" should check
        finish_reason directly.
        """
        return self.finish_reason in TRUNCATION_FINISH_REASONS


class Model(ABC):
    """Abstract base class for all model backends.

    Subclasses must implement generate(). See the module docstring for why
    the interface deliberately excludes sampling controls.
    """

    def __init__(self, model_name: str):
        self.model_name = model_name

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 500,
    ) -> GenerationOutput:
        """Generate a completion for the given prompt.

        Args:
            prompt: The input text.
            max_new_tokens: Maximum tokens for the VISIBLE answer. Backends
                for reasoning-capable models add their own internal
                reasoning buffer on top of this when constructing the
                provider's actual token cap — callers do not need to
                account for reasoning tokens themselves.

        Returns:
            GenerationOutput with at least `text` populated, and
            `finish_reason` populated for every backend whose provider
            reports one.
        """
        ...
