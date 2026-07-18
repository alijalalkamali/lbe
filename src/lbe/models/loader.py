"""Factory for constructing model backends from a name string.

Eval code calls load_model(name) instead of importing a specific class. The
factory chooses the right backend based on the name, so adding new backends
later doesn't require eval code changes.

Naming conventions:
    Local HuggingFace: "org/model" (e.g., "Qwen/Qwen2.5-0.5B-Instruct")
    API models: "provider:model" where provider is one of anthropic, openai,
        deepseek, together, google. Examples:
            "anthropic:claude-opus-4-7"
            "openai:gpt-5"
            "openai:o4-mini"
            "deepseek:deepseek-reasoner"
            "together:meta-llama/Llama-3.3-70B-Instruct-Turbo"
            "google:gemini-3.5-pro"
"""

from lbe.models.base import Model
from lbe.models.local import LocalHFModel


def load_model(model_name: str, **kwargs) -> Model:
    """Construct the appropriate Model backend for the given name.

    Args:
        model_name: Either a HuggingFace repo ID ("org/model") for local
            models, or a "provider:model" string for API-backed models.
        **kwargs: Backend-specific options passed through to the underlying
            class. For LocalHFModel: device, dtype. For API backends:
            api_key, timeout.

    Returns:
        An instantiated Model ready for generation.

    Raises:
        ValueError: If the name doesn't match any known backend.
    """
    # API model routing via "provider:" prefix
    if ":" in model_name:
        provider, model_id = model_name.split(":", 1)

        if provider == "anthropic":
            from lbe.models.anthropic_backend import AnthropicBackend

            return AnthropicBackend(model_id, **kwargs)

        if provider == "openai":
            from lbe.models.openai_backend import OpenAIBackend

            return OpenAIBackend(model_id, **kwargs)

        if provider == "deepseek":
            from lbe.models.deepseek_backend import DeepSeekBackend

            return DeepSeekBackend(model_id, **kwargs)

        if provider == "together":
            from lbe.models.together_backend import TogetherBackend

            return TogetherBackend(model_id, **kwargs)

        if provider == "google":
            from lbe.models.google_backend import GoogleBackend

            return GoogleBackend(model_id, **kwargs)

        raise ValueError(
            f"Unknown API provider {provider!r} in {model_name!r}. "
            "Supported providers: anthropic, openai, deepseek, together, google."
        )

    # Local HuggingFace model routing
    if "/" in model_name:
        return LocalHFModel(model_name, **kwargs)

    raise ValueError(
        f"Cannot determine backend for {model_name!r}. "
        "Expected either 'provider:model' for API backends or "
        "'org/model' for HuggingFace local models."
    )
