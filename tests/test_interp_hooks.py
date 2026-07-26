"""
Tests for ActivationCache using dummy nn.Modules.

These validate the hook mechanism itself (capture correctness, cleanup,
error handling) without needing real model weights -- the same logic runs
unchanged against Llama's actual decoder layers.
"""

from __future__ import annotations

import pytest
import torch
import torch.nn as nn

from lbe.interp.hooks import ActivationCache


class TupleOutputLayer(nn.Module):
    """Mimics HF decoder layers that return (hidden_states, ...) tuples."""

    def __init__(self, hidden_dim: int, add_value: float) -> None:
        super().__init__()
        self.add_value = add_value

    def forward(self, x: torch.Tensor):
        return (x + self.add_value, None)  # second element mimics e.g. attn weights


class TensorOutputLayer(nn.Module):
    """Mimics decoder layers that return a bare tensor (no tuple wrapping)."""

    def __init__(self, add_value: float) -> None:
        super().__init__()
        self.add_value = add_value

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.add_value


class BadOutputLayer(nn.Module):
    """Returns something that isn't a tensor or tensor-first tuple."""

    def forward(self, x: torch.Tensor):
        return {"hidden": x}


class ToyModel(nn.Module):
    """
    Mimics a real HF causal LM's decoder stack: each layer may return a
    tuple, but the MODEL's own forward loop always unwraps to the tensor
    before feeding the next layer -- the tuple wrapping is only visible to
    hooks observing that one layer's raw output, never to downstream layers.
    """

    def __init__(self, layers: list[nn.Module]) -> None:
        super().__init__()
        self.layers = nn.ModuleList(layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        for layer in self.layers:
            out = layer(x)
            x = out[0] if isinstance(out, tuple) else out
        return x


def test_captures_correct_values_tuple_output():
    # 3 layers, each adds a distinct constant -> lets us verify per-layer
    # capture isn't cross-contaminated.
    model = ToyModel([TupleOutputLayer(4, add_value=v) for v in (1.0, 10.0, 100.0)])
    x = torch.zeros(1, 2, 4)

    with ActivationCache(model.layers, layer_indices=[0, 1, 2]) as cache:
        model(x)
        assert torch.allclose(cache.get(0), torch.full((1, 2, 4), 1.0))
        assert torch.allclose(cache.get(1), torch.full((1, 2, 4), 11.0))  # cumulative
        assert torch.allclose(cache.get(2), torch.full((1, 2, 4), 111.0))


def test_captures_correct_values_bare_tensor_output():
    model = ToyModel([TensorOutputLayer(add_value=v) for v in (2.0, 3.0)])
    x = torch.zeros(1, 1, 4)

    with ActivationCache(model.layers, layer_indices=[0, 1]) as cache:
        model(x)
        assert torch.allclose(cache.get(0), torch.full((1, 1, 4), 2.0))
        assert torch.allclose(cache.get(1), torch.full((1, 1, 4), 5.0))


def test_partial_layer_selection_only_captures_requested():
    model = ToyModel([TensorOutputLayer(add_value=v) for v in (1.0, 1.0, 1.0)])
    x = torch.zeros(1, 1, 2)

    with ActivationCache(model.layers, layer_indices=[1]) as cache:
        model(x)
        assert cache.get(1) is not None
        with pytest.raises(KeyError):
            cache.get(0)
        with pytest.raises(KeyError):
            cache.get(2)


def test_clear_drops_captures_but_keeps_hooks_registered():
    model = ToyModel([TensorOutputLayer(add_value=5.0)])
    x = torch.zeros(1, 1, 2)

    with ActivationCache(model.layers, layer_indices=[0]) as cache:
        model(x)
        cache.clear()
        with pytest.raises(KeyError):
            cache.get(0)
        model(x)  # hooks still registered after clear()
        assert torch.allclose(cache.get(0), torch.full((1, 1, 2), 5.0))


def test_hooks_removed_on_exit_no_leak_across_context_reuse():
    model = ToyModel([TensorOutputLayer(add_value=1.0)])
    x = torch.zeros(1, 1, 2)

    with ActivationCache(model.layers, layer_indices=[0]):
        model(x)
    assert len(model.layers[0]._forward_hooks) == 0, (
        "Hook was not removed on context exit -- repeated harvest() calls "
        "would silently accumulate duplicate hooks on the same module."
    )

    # A second, independent context should work cleanly (no interference
    # from a leaked prior hook).
    with ActivationCache(model.layers, layer_indices=[0]) as cache2:
        model(x)
        assert torch.allclose(cache2.get(0), torch.full((1, 1, 2), 1.0))


def test_bad_output_type_raises_typeerror():
    model = ToyModel([BadOutputLayer()])
    x = torch.zeros(1, 1, 2)

    with ActivationCache(model.layers, layer_indices=[0]):
        with pytest.raises(TypeError, match="expected a tensor"):
            model(x)


def test_out_of_range_layer_index_raises_at_construction():
    model = ToyModel([TensorOutputLayer(add_value=1.0)])
    with pytest.raises(ValueError, match="out of range"):
        ActivationCache(model.layers, layer_indices=[0, 5])


def test_empty_layer_indices_raises():
    model = ToyModel([TensorOutputLayer(add_value=1.0)])
    with pytest.raises(ValueError, match="non-empty"):
        ActivationCache(model.layers, layer_indices=[])


def test_captures_detached_tensors_not_graph_connected():
    model = ToyModel([TensorOutputLayer(add_value=1.0)])
    x = torch.zeros(1, 1, 2, requires_grad=True)

    with ActivationCache(model.layers, layer_indices=[0]) as cache:
        out = model(x)
        out.sum().backward()  # would error if detach() interfered with the real graph
        assert not cache.get(0).requires_grad
