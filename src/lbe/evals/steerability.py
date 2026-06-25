"""Steerability eval: measure whether a model changes behavior on instruction.

For each item, the model is run on:
  - the base prompt alone (default behavior)
  - the base prompt with a steering instruction (target behavior)

A scorer measures both responses on a category-appropriate metric, then the
delta is computed. The score is whether the metric shifted in the expected
direction.

This module is intentionally model-agnostic: it accepts any Model instance
from lbe.models, so the same eval runs against local HuggingFace models or
future API backends.
"""

from lbe.evals.scorers.rule_based import measure
from lbe.io.dataset import EvalResult, SteerabilityItem
from lbe.models.base import Model

# Per-category expected direction of metric change after steering.
# +1 means the steered metric should be HIGHER than the base metric.
# -1 means the steered metric should be LOWER than the base metric.
# 0 means we measure absolute change only (direction not predicted).
EXPECTED_DIRECTION: dict[str, int] = {
    "length_control": -1,  # steering asks for shorter responses
    "format": 0,  # format is categorical; direction not meaningful
}


def run_steerability_item(
    item: SteerabilityItem,
    model: Model,
    max_new_tokens: int = 256,
    temperature: float = 0.0,
    seed: int | None = 42,
) -> EvalResult:
    """Run one steerability item against one model and score it.

    Generates two responses (base, steered), measures both, and computes
    a score in [0, 1] indicating whether steering moved the metric in the
    expected direction. Returns None for the score field if the item's
    category has no rule-based scorer (LLM-judge needed).
    """
    base_output = model.generate(
        prompt=item.base_prompt,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        seed=seed,
    )
    steered_output = model.generate(
        prompt=item.steering_instruction,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        seed=seed,
    )

    base_metric = measure(item.category, base_output.text)
    steered_metric = measure(item.category, steered_output.text)

    score = _compute_score(item.category, base_metric, steered_metric)

    return EvalResult(
        item_id=item.id,
        item_type=item.item_type,
        model_name=model.model_name,
        seed=seed,
        raw_completions=[base_output.text, steered_output.text],
        score=score,
        extra={
            "category": item.category,
            "base_metric": base_metric,
            "steered_metric": steered_metric,
            "expected_direction": EXPECTED_DIRECTION.get(item.category, 0),
        },
    )


def _compute_score(
    category: str,
    base_metric: float | None,
    steered_metric: float | None,
) -> float | None:
    """Score in [0, 1] for whether steering shifted the metric as expected.

    Returns None when either metric is unscorable (LLM-judge needed).
    """
    if base_metric is None or steered_metric is None:
        return None

    direction = EXPECTED_DIRECTION.get(category, 0)
    delta = steered_metric - base_metric

    if direction == 0:
        # Direction not predicted — score on whether anything changed.
        return 1.0 if delta != 0 else 0.0

    # Expected directional change.
    if direction > 0:
        return 1.0 if delta > 0 else 0.0
    else:
        return 1.0 if delta < 0 else 0.0


def run_steerability_eval(
    items: list[SteerabilityItem],
    model: Model,
    **kwargs,
) -> list[EvalResult]:
    """Run the steerability eval across a list of items and return results."""
    return [run_steerability_item(item, model, **kwargs) for item in items]
