"""
Linear probing with a permutation-tested null, per layer.

Statistical design (each piece is load-bearing at n~100, d=8192):

  - Held-out accuracy via stratified k-fold: the reported number is always
    from folds never used for fitting. Stratification keeps the 42:58 class
    ratio in every fold, which matters at this n.
  - L2 regularization, strength chosen by NESTED CV: the inner loop picks C
    using only the outer-training portion, so hyperparameter selection never
    sees the fold it is evaluated on. Un-nested tuning quietly inflates
    accuracy.
  - Permutation null: shuffle labels, rerun the ENTIRE nested-CV pipeline,
    repeat n_permutations times. The real accuracy's empirical p-value is
    (1 + #{perm >= real}) / (1 + n_permutations)  [Phipson & Smyth 2010 --
    the +1s make the estimate valid, never exactly zero]. At n<<d a probe
    can separate anything, so accuracy alone is meaningless without this null.
  - Balanced accuracy as the metric: with a 42:58 split, raw accuracy of
    0.58 is achievable by always predicting the majority class; balanced
    accuracy (mean of per-class recalls) makes chance = 0.5 regardless of
    imbalance, which also makes the permutation distribution center where
    intuition expects.

Everything is seeded and single-threaded deterministic; results are exactly
reproducible from (activations file, labels, seed).
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

# C = 1/lambda in sklearn's parameterization: SMALLER C = STRONGER penalty.
# Grid spans 4 orders of magnitude around the heavily-regularized regime
# appropriate for n<<d.
DEFAULT_C_GRID = (1e-4, 1e-3, 1e-2, 1e-1, 1.0)


@dataclass(frozen=True)
class LayerProbeResult:
    layer_index: int
    real_balanced_accuracy: float
    permutation_mean: float
    permutation_std: float
    p_value: float
    n_examples: int
    n_positive: int
    n_permutations: int
    outer_folds: int
    inner_folds: int


def _nested_cv_balanced_accuracy(
    X: np.ndarray,
    y: np.ndarray,
    seed: int,
    outer_folds: int,
    inner_folds: int,
    c_grid: tuple[float, ...],
) -> float:
    """
    One full nested-CV evaluation -> held-out balanced accuracy.

    Standardization is INSIDE the pipeline so per-fold scaling statistics
    are computed on training data only -- scaling on the full dataset before
    splitting is a subtle leak (test-fold means/variances influence the
    transform applied to training data).
    """
    pipeline = Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "clf",
                LogisticRegression(solver="liblinear", max_iter=5000, random_state=seed),
            ),
        ]
    )
    inner = StratifiedKFold(n_splits=inner_folds, shuffle=True, random_state=seed)
    search = GridSearchCV(
        pipeline,
        param_grid={"clf__C": list(c_grid)},
        scoring="balanced_accuracy",
        cv=inner,
        n_jobs=1,
    )
    outer = StratifiedKFold(n_splits=outer_folds, shuffle=True, random_state=seed + 1)
    y_pred = cross_val_predict(search, X, y, cv=outer, n_jobs=1)
    return float(balanced_accuracy_score(y, y_pred))


def probe_layer(
    X: np.ndarray,
    y: np.ndarray,
    layer_index: int,
    n_permutations: int = 200,
    seed: int = 0,
    outer_folds: int = 5,
    inner_folds: int = 3,
    c_grid: tuple[float, ...] = DEFAULT_C_GRID,
) -> LayerProbeResult:
    """Real nested-CV accuracy + permutation null for one layer's activations."""
    if X.ndim != 2:
        raise ValueError(f"X must be [n_examples, hidden_dim], got shape {X.shape}")
    if len(X) != len(y):
        raise ValueError(f"X has {len(X)} rows but y has {len(y)} labels")
    y = np.asarray(y)
    classes, counts = np.unique(y, return_counts=True)
    if len(classes) != 2:
        raise ValueError(f"y must be binary, got classes {classes}")
    if counts.min() < outer_folds:
        raise ValueError(
            f"Minority class has {counts.min()} examples < outer_folds={outer_folds}; "
            f"stratified {outer_folds}-fold CV is impossible. Reduce folds or rethink."
        )

    real = _nested_cv_balanced_accuracy(X, y, seed, outer_folds, inner_folds, c_grid)

    rng = np.random.default_rng(seed)
    perm_scores = np.empty(n_permutations)
    for i in range(n_permutations):
        y_perm = rng.permutation(y)
        perm_scores[i] = _nested_cv_balanced_accuracy(
            X, y_perm, seed, outer_folds, inner_folds, c_grid
        )
        if (i + 1) % 25 == 0:
            logger.info("Layer %d: permutation %d/%d", layer_index, i + 1, n_permutations)

    p_value = float((1 + np.sum(perm_scores >= real)) / (1 + n_permutations))

    return LayerProbeResult(
        layer_index=layer_index,
        real_balanced_accuracy=real,
        permutation_mean=float(perm_scores.mean()),
        permutation_std=float(perm_scores.std()),
        p_value=p_value,
        n_examples=len(y),
        n_positive=int(counts[classes == 1][0]) if 1 in classes else 0,
        n_permutations=n_permutations,
        outer_folds=outer_folds,
        inner_folds=inner_folds,
    )


def probe_all_layers(
    activations_path: Path,
    item_labels: dict[str, int],
    output_path: Path,
    n_permutations: int = 200,
    seed: int = 0,
) -> list[LayerProbeResult]:
    """
    Run probe_layer for every harvested layer; write results as JSON.

    activations_path: torch.save'd dict[item_id -> dict[layer_idx -> np.ndarray]]
    item_labels: item_id -> 0/1, from data.binary_labels + the same examples.
    Items present in activations but absent from labels (or vice versa) are a
    hard error: the two must describe the same example set exactly.
    """
    import torch

    store: dict[str, dict[int, np.ndarray]] = torch.load(activations_path, weights_only=False)

    act_ids = set(store)
    label_ids = set(item_labels)
    if act_ids != label_ids:
        raise ValueError(
            f"Activation/label mismatch: {len(act_ids - label_ids)} item(s) only in "
            f"activations {sorted(act_ids - label_ids)[:5]}...; "
            f"{len(label_ids - act_ids)} only in labels {sorted(label_ids - act_ids)[:5]}..."
        )

    item_order = sorted(store)
    y = np.array([item_labels[i] for i in item_order])

    layer_sets = {frozenset(store[i]) for i in item_order}
    if len(layer_sets) != 1:
        raise ValueError("Inconsistent layer sets across items in the activation store.")
    layer_indices = sorted(next(iter(layer_sets)))

    results: list[LayerProbeResult] = []
    for layer_idx in layer_indices:
        X = np.stack([store[i][layer_idx] for i in item_order])
        result = probe_layer(X, y, layer_idx, n_permutations=n_permutations, seed=seed)
        results.append(result)
        logger.info(
            "Layer %d: real=%.3f perm=%.3f±%.3f p=%.4f",
            layer_idx,
            result.real_balanced_accuracy,
            result.permutation_mean,
            result.permutation_std,
            result.p_value,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps([asdict(r) for r in results], indent=2))
    logger.info("Wrote %d layer results to %s", len(results), output_path)
    return results
