"""
Tests for lbe.interp.data (join logic, against the real lbe.io schemas) and
lbe.interp.probe (statistical behavior on synthetic data with known truth).

The probe tests are the important ones conceptually: they verify the
pipeline finds signal when signal exists by construction, and -- the case
that actually matters at n<<d -- REFUSES to find signal in pure noise.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from lbe.interp.data import binary_labels, build_probe_examples
from lbe.interp.probe import probe_layer
from lbe.io.dataset import EvalResult, SteerabilityItem
from lbe.io.jsonl import write_jsonl

RESPONDER = "together:meta-llama/Llama-3.3-70B-Instruct-Turbo"
CATEGORY = "values_conflict_low"


def _make_fixture(tmp_path: Path, n: int = 6):
    items = [
        SteerabilityItem(
            id=f"vcl_{i:03d}",
            category=CATEGORY,
            base_prompt=f"base prompt {i}",
            steering_instruction=f"steered prompt {i}",
            expected_behavior_change="n/a",
        )
        for i in range(n)
    ]
    results = [
        EvalResult(
            item_id=f"vcl_{i:03d}",
            item_type="steerability",
            model_name=RESPONDER,
            seed=None,
            raw_completions=[f"base response {i}", f"steered response {i}"],
            finish_reasons=["stop", "stop"],
            score=None,
            extra={"category": CATEGORY},
        )
        for i in range(n)
    ]
    items_path = tmp_path / "items.jsonl"
    results_path = tmp_path / "results.jsonl"
    write_jsonl(items_path, items)
    write_jsonl(results_path, results)

    csv_path = tmp_path / "aggregated_judgments.csv"
    header = "item_id,category,responder_model,condition,consensus_loo\n"
    rows = [
        f"vcl_{i:03d},{CATEGORY},{RESPONDER},base,"
        + ("derail" if i % 2 == 0 else "full-compliance")
        + "\n"
        for i in range(n)
    ]
    csv_path.write_text(header + "".join(rows))
    return items_path, results_path, csv_path


class TestJoin:
    def test_joins_and_selects_base_completion(self, tmp_path: Path):
        items_path, results_path, csv_path = _make_fixture(tmp_path)
        examples = build_probe_examples(
            items_path,
            results_path,
            csv_path,
            category=CATEGORY,
            condition="base",
            responder_model=RESPONDER,
        )
        assert len(examples) == 6
        ex = next(e for e in examples if e.item_id == "vcl_000")
        assert ex.prompt_text == "base prompt 0"  # base_prompt, not steering
        assert ex.response_text == "base response 0"  # raw_completions[0]
        assert ex.consensus_loo == "derail"

    def test_steered_condition_uses_steering_instruction_and_index_1(self, tmp_path: Path):
        items_path, results_path, csv_path = _make_fixture(tmp_path)
        csv_path.write_text(
            "item_id,category,responder_model,condition,consensus_loo\n"
            f"vcl_000,{CATEGORY},{RESPONDER},steered,full-compliance\n"
        )
        examples = build_probe_examples(
            items_path,
            results_path,
            csv_path,
            category=CATEGORY,
            condition="steered",
            responder_model=RESPONDER,
        )
        assert examples[0].prompt_text == "steered prompt 0"
        assert examples[0].response_text == "steered response 0"

    def test_missing_result_is_hard_error(self, tmp_path: Path):
        items_path, results_path, csv_path = _make_fixture(tmp_path)
        # Add a consensus row for an item with no logged response
        with csv_path.open("a") as f:
            f.write(f"vcl_999,{CATEGORY},{RESPONDER},base,derail\n")
        # Also add the item definition so only the RESULT is missing
        items = [
            SteerabilityItem(
                id="vcl_999",
                category=CATEGORY,
                base_prompt="x",
                steering_instruction="y",
                expected_behavior_change="n/a",
            )
        ]
        with items_path.open("a") as f:
            for it in items:
                f.write(it.model_dump_json() + "\n")
        with pytest.raises(ValueError, match="Join incomplete"):
            build_probe_examples(
                items_path,
                results_path,
                csv_path,
                category=CATEGORY,
                condition="base",
                responder_model=RESPONDER,
            )

    def test_invalid_condition_rejected(self, tmp_path: Path):
        items_path, results_path, csv_path = _make_fixture(tmp_path)
        with pytest.raises(ValueError, match="condition must be one of"):
            build_probe_examples(
                items_path,
                results_path,
                csv_path,
                category=CATEGORY,
                condition="steeered",
                responder_model=RESPONDER,
            )

    def test_binary_labels_and_degenerate_guard(self, tmp_path: Path):
        items_path, results_path, csv_path = _make_fixture(tmp_path)
        examples = build_probe_examples(
            items_path,
            results_path,
            csv_path,
            category=CATEGORY,
            condition="base",
            responder_model=RESPONDER,
        )
        y = binary_labels(examples, positive_label="derail")
        assert sum(y) == 3
        with pytest.raises(ValueError, match="Degenerate"):
            binary_labels(examples, positive_label="nonexistent-label")


class TestProbeStatistics:
    """Synthetic-truth tests: known signal must be found, pure noise must not."""

    def _synthetic(self, n: int, d: int, signal: bool, seed: int = 7):
        rng = np.random.default_rng(seed)
        y = np.array([0] * (n // 2) + [1] * (n - n // 2))
        X = rng.standard_normal((n, d))
        if signal:
            # Distributed signal: a concept DIRECTION spanning many dims
            # (mean shift of 0.8 on the first 20), matching what real
            # residual-stream representations look like. A single-dimension
            # needle is intentionally NOT used: a regularized probe at this
            # n rightly cannot find 1 informative dim among hundreds, and
            # that is desired behavior, not a failure.
            X[y == 1, :20] += 0.8
        return X, y

    def test_finds_real_signal(self):
        X, y = self._synthetic(n=60, d=200, signal=True)
        result = probe_layer(X, y, layer_index=0, n_permutations=50, seed=0)
        assert result.real_balanced_accuracy > 0.8
        assert result.p_value < 0.05

    def test_rejects_pure_noise_at_n_much_less_than_d(self):
        # THE critical property: d >> n and zero signal -- accuracy must land
        # near the permutation distribution, p must NOT be significant.
        X, y = self._synthetic(n=40, d=500, signal=False)
        result = probe_layer(X, y, layer_index=0, n_permutations=50, seed=0)
        assert result.p_value > 0.05
        assert abs(result.real_balanced_accuracy - result.permutation_mean) < 0.15

    def test_pvalue_never_zero(self):
        X, y = self._synthetic(n=60, d=50, signal=True)
        result = probe_layer(X, y, layer_index=0, n_permutations=20, seed=0)
        assert result.p_value >= 1 / 21  # Phipson-Smyth floor

    def test_shape_and_class_guards(self):
        X, y = self._synthetic(n=40, d=20, signal=False)
        with pytest.raises(ValueError, match="binary"):
            probe_layer(X, np.zeros(40, dtype=int), layer_index=0, n_permutations=5)
        with pytest.raises(ValueError, match="rows"):
            probe_layer(X, y[:-1], layer_index=0, n_permutations=5)
        with pytest.raises(ValueError, match="n_examples, hidden_dim"):
            probe_layer(X.ravel(), y, layer_index=0, n_permutations=5)

    def test_minority_class_smaller_than_folds_rejected(self):
        rng = np.random.default_rng(0)
        X = rng.standard_normal((20, 10))
        y = np.array([1] * 3 + [0] * 17)  # 3 < 5 outer folds
        with pytest.raises(ValueError, match="Minority class"):
            probe_layer(X, y, layer_index=0, n_permutations=5)

    def test_deterministic_given_seed(self):
        X, y = self._synthetic(n=40, d=30, signal=True)
        r1 = probe_layer(X, y, layer_index=0, n_permutations=10, seed=3)
        r2 = probe_layer(X, y, layer_index=0, n_permutations=10, seed=3)
        assert r1 == r2
