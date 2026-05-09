"""Factory for constructing model backends from a name string.

Eval code calls load_model(name) instead of importing a specific class. The
factory chooses the right backend based on the name, so adding new backends
later (Anthropic API, vLLM, etc.) doesn't require eval code changes.
"""

from lbe.models.base import Model
from lbe.models.local import LocalHFModel


def load_model(model_name: str, **kwargs) -> Model:
    """Construct the appropriate Model backend for the given name.

    Args:
        model_name: HuggingFace repo ID (e.g., "Qwen/Qwen2.5-0.5B-Instruct")
            or a future API model name. Currently only HuggingFace IDs are
            supported.
        **kwargs: Backend-specific options passed through to the underlying
            class. For LocalHFModel: device, dtype.

    Returns:
        An instantiated Model ready for generation.

    Raises:
        ValueError: If the name doesn't match any known backend.
    """
    if "/" in model_name:
        # HuggingFace IDs always have the form "org/model"
        return LocalHFModel(model_name, **kwargs)

    raise ValueError(
        f"Cannot determine backend for {model_name!r}. "
        "HuggingFace IDs must contain '/' (e.g., 'Qwen/Qwen2.5-0.5B-Instruct')."
    )
