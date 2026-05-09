"""Base classes and types for the model abstraction layer.

Every model backend (local HuggingFace models, Anthropic API, etc.) implements
the Model interface defined here. Eval code calls model.generate(prompt) and
gets back a GenerationOutput, regardless of which backend produced it.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class GenerationOutput:
    """Structured output from a single model generation call.

    Some fields are only populated by certain backends:
    - text: always populated
    - logprobs: only by local backends with return_logprobs=True
    - hidden_states: only by local backends with return_hidden_states=True

    API backends leave the optional fields as None.
    """

    text: str
    prompt: str
    model_name: str
    logprobs: list[float] | None = field(default=None)
    hidden_states: list | None = field(default=None)


class Model(ABC):
    """Abstract base class for all model backends.

    Subclasses must implement generate(). The interface intentionally accepts
    only what every backend can support; backend-specific options can be set
    at construction time.
    """

    def __init__(self, model_name: str):
        self.model_name = model_name

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 1.0,
        seed: int | None = None,
    ) -> GenerationOutput:
        """Generate a completion for the given prompt.

        Args:
            prompt: The input text.
            max_new_tokens: Maximum number of tokens to generate (excluding prompt).
            temperature: Sampling temperature. 0.0 means greedy/deterministic.
            seed: Random seed for reproducibility, when supported by the backend.

        Returns:
            GenerationOutput with at least the text field populated.
        """
        ...
