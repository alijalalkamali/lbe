"""
Tests for lbe.interp.steer: split logic, vector construction, and the
steering hook's addition mechanics -- all against synthetic data and dummy
modules, no model download required.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch
import torch.nn as nn

from lbe.interp.steer import (
    SteeringHook,
    build_steering_vector,
    report_residual_norms,
    split_items,
)


def _fake_store(n: int = 20, d: int = 8, layer: int = 4, seed: int = 0):
    """n items, half 'derail', activations with a known class offset."""
    rng = np.random.default_rng(seed)
    activations, labels = {}, {}
    for i in range(n):
        item_id = f"vcl_{i:03d}"
        label = "derail" if i < n // 2 else "full-compliance"
        vec = rng.standard_normal(d).astype(np.float32)
        if label == "derail":
            vec[0] += 5.0  # known direction: dimension 0
        activations[item_id] = {layer: vec}
        labels[item_id] = label
    return activations, labels


class TestSplit:
    def test_disjoint_exhaustive_stratified(self):
        _, labels = _fake_store(n=20)
        ids = sorted(labels)
        vec_items, eval_items = split_items(ids, labels, "derail", 0.5, seed=1)
        assert set(vec_items).isdisjoint(eval_items)
        assert sorted(vec_items + eval_items) == ids
        # stratification: both splits contain both classes
        for split in (vec_items, eval_items):
            split_labels = {labels[i] for i in split}
            assert split_labels == {"derail", "full-compliance"}

    def test_deterministic_given_seed(self):
        _, labels = _fake_store(n=20)
        ids = sorted(labels)
        assert split_items(ids, labels, "derail", 0.5, seed=7) == split_items(
            ids, labels, "derail", 0.5, seed=7
        )
        assert split_items(ids, labels, "derail", 0.5, seed=7) != split_items(
            ids, labels, "derail", 0.5, seed=8
        )

    def test_single_class_rejected(self):
        labels = {"a": "derail", "b": "derail"}
        with pytest.raises(ValueError, match="Split impossible"):
            split_items(["a", "b"], labels, "derail")

    def test_extreme_fraction_keeps_both_splits_nonempty_per_class(self):
        _, labels = _fake_store(n=6)
        ids = sorted(labels)
        vec_items, eval_items = split_items(ids, labels, "derail", 0.9, seed=0)
        for split in (vec_items, eval_items):
            assert {labels[i] for i in split} == {"derail", "full-compliance"}

    def test_bad_fraction_rejected(self):
        _, labels = _fake_store(n=4)
        with pytest.raises(ValueError, match="vector_fraction"):
            split_items(sorted(labels), labels, "derail", 1.0)


class TestVector:
    def test_recovers_known_direction_unit_norm(self):
        activations, labels = _fake_store(n=20, d=8, layer=4)
        vec_items, _ = split_items(sorted(labels), labels, "derail", 0.5, seed=0)
        sv = build_steering_vector(activations, labels, 4, "derail", vec_items)
        assert np.isclose(np.linalg.norm(sv.vector), 1.0, atol=1e-5)
        # dominant component must be the planted dimension 0, positive sign
        assert np.argmax(np.abs(sv.vector)) == 0
        assert sv.vector[0] > 0.5

    def test_provenance_recorded(self):
        activations, labels = _fake_store(n=10)
        vec_items, _ = split_items(sorted(labels), labels, "derail", 0.5, seed=0)
        sv = build_steering_vector(activations, labels, 4, "derail", vec_items)
        assert sv.vector_item_ids == tuple(vec_items)
        assert sv.n_positive + sv.n_negative == len(vec_items)

    def test_missing_layer_rejected(self):
        activations, labels = _fake_store(n=10, layer=4)
        vec_items, _ = split_items(sorted(labels), labels, "derail", 0.5, seed=0)
        with pytest.raises(ValueError, match="Layer 99"):
            build_steering_vector(activations, labels, 99, "derail", vec_items)

    def test_single_class_vector_split_rejected(self):
        activations, labels = _fake_store(n=10)
        only_derail = [i for i in sorted(labels) if labels[i] == "derail"]
        with pytest.raises(ValueError, match="both classes"):
            build_steering_vector(activations, labels, 4, "derail", only_derail)

    def test_residual_norm_report(self):
        activations, _ = _fake_store(n=10, d=8, layer=4)
        assert report_residual_norms(activations, 4) > 0
        with pytest.raises(ValueError, match="No harvested"):
            report_residual_norms(activations, 99)


class _TupleLayer(nn.Module):
    def forward(self, x):
        return (x, "extra")


class _BareLayer(nn.Module):
    def forward(self, x):
        return x


class TestSteeringHook:
    def test_adds_alpha_v_tuple_output(self):
        layer = _TupleLayer()
        v = np.zeros(4, dtype=np.float32)
        v[1] = 1.0
        x = torch.zeros(1, 3, 4)
        with SteeringHook(layer, v, alpha=2.5):
            out, extra = layer(x)
        assert extra == "extra"
        expected = torch.zeros(1, 3, 4)
        expected[:, :, 1] = 2.5  # added at EVERY position
        assert torch.allclose(out, expected)

    def test_adds_alpha_v_bare_output(self):
        layer = _BareLayer()
        v = np.ones(4, dtype=np.float32)
        x = torch.zeros(1, 2, 4)
        with SteeringHook(layer, v, alpha=-1.0):
            out = layer(x)
        assert torch.allclose(out, torch.full((1, 2, 4), -1.0))

    def test_alpha_zero_is_exact_identity(self):
        layer = _BareLayer()
        v = np.ones(4, dtype=np.float32)
        x = torch.randn(1, 5, 4)
        with SteeringHook(layer, v, alpha=0.0):
            out = layer(x)
        assert out is x  # not even a numerically-equal copy: the same tensor

    def test_set_alpha_between_passes(self):
        layer = _BareLayer()
        v = np.ones(2, dtype=np.float32)
        x = torch.zeros(1, 1, 2)
        with SteeringHook(layer, v, alpha=1.0) as hook:
            assert torch.allclose(layer(x), torch.ones(1, 1, 2))
            hook.set_alpha(3.0)
            assert torch.allclose(layer(x), torch.full((1, 1, 2), 3.0))

    def test_dim_mismatch_raises(self):
        layer = _BareLayer()
        v = np.ones(3, dtype=np.float32)  # hidden dim is 4
        x = torch.zeros(1, 1, 4)
        with SteeringHook(layer, v, alpha=1.0):
            with pytest.raises(ValueError, match="vector dim 3 != hidden dim 4"):
                layer(x)

    def test_hook_removed_on_exit(self):
        layer = _BareLayer()
        v = np.ones(4, dtype=np.float32)
        x = torch.zeros(1, 1, 4)
        with SteeringHook(layer, v, alpha=5.0):
            pass
        assert torch.allclose(layer(x), x)  # no steering after exit
        assert len(layer._forward_hooks) == 0

    def test_dtype_follows_hidden_states(self):
        layer = _BareLayer()
        v = np.ones(4, dtype=np.float32)
        x = torch.zeros(1, 1, 4, dtype=torch.float16)
        with SteeringHook(layer, v, alpha=1.0):
            out = layer(x)
        assert out.dtype == torch.float16
