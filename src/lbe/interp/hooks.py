"""
Residual-stream activation capture via forward hooks.

A forward hook is a callback PyTorch invokes automatically every time a given
module completes its forward pass, handing the callback that module's output.
We attach one hook per target decoder layer; each hook just copies the
output tensor into a dict (harvesting), never modifying it.

Works with any HF causal LM whose decoder layers are an indexable list of
modules (Llama, Qwen, Mistral all expose this at `model.model.layers`) --
the wrapping decoder layer's forward always returns the post-layer residual
stream as the first element, but WHETHER it's wrapped in a tuple varies by
transformers version, so we defensively unwrap both cases.
"""

from __future__ import annotations

from types import TracebackType

import torch
import torch.nn as nn


class ActivationCache:
    """
    Context manager: registers forward hooks on entry, removes them on exit.

    Usage:
        with ActivationCache(model.model.layers, layer_indices=[0, 4, 8]) as cache:
            model(input_ids)
            layer0_acts = cache.get(0)  # shape [batch, seq_len, hidden_dim]

    Hooks MUST be removed after use -- leaving them attached across repeated
    calls silently accumulates duplicate hooks on the same module, each of
    which fires again on every subsequent forward pass. The context-manager
    pattern makes that leak structurally impossible rather than relying on
    the caller to remember `.remove()`.
    """

    def __init__(self, layers: nn.ModuleList, layer_indices: list[int]) -> None:
        if not layer_indices:
            raise ValueError("layer_indices must be non-empty")
        n_layers = len(layers)
        bad = [i for i in layer_indices if not (0 <= i < n_layers)]
        if bad:
            raise ValueError(f"layer indices out of range for {n_layers}-layer model: {bad}")

        self._layers = layers
        self._layer_indices = list(layer_indices)
        self._handles: list[torch.utils.hooks.RemovableHandle] = []
        self._captured: dict[int, torch.Tensor] = {}

    def _make_hook(self, layer_idx: int):
        def hook(module: nn.Module, inputs: tuple, output):
            hidden = output[0] if isinstance(output, tuple) else output
            if not torch.is_tensor(hidden):
                raise TypeError(
                    f"Layer {layer_idx} hook expected a tensor (or tuple with a "
                    f"tensor first element), got {type(hidden)}. The decoder "
                    f"layer's output format may differ for this model class -- "
                    f"inspect `model.model.layers[{layer_idx}].forward` before proceeding."
                )
            self._captured[layer_idx] = hidden.detach()

        return hook

    def __enter__(self) -> ActivationCache:
        for idx in self._layer_indices:
            handle = self._layers[idx].register_forward_hook(self._make_hook(idx))
            self._handles.append(handle)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        for handle in self._handles:
            handle.remove()
        self._handles = []

    def get(self, layer_idx: int) -> torch.Tensor:
        if layer_idx not in self._captured:
            raise KeyError(
                f"No activation captured for layer {layer_idx}. Either the "
                f"forward pass hasn't run yet, or this layer wasn't in "
                f"layer_indices."
            )
        return self._captured[layer_idx]

    def clear(self) -> None:
        """Drop captured activations between examples without touching hooks."""
        self._captured = {}

    @property
    def layer_indices(self) -> list[int]:
        return list(self._layer_indices)
