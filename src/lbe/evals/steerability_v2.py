"""V2 steerability eval - response generation only, scoring deferred.

V2 expands beyond v1's rule-based scoring categories. This module
generates base and steered responses on each item and saves raw outputs
as JSONL. Scoring (rule-based for rh items, LLM judge for others) is
applied as a separate downstream step.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lbe.io.dataset import EvalResult, SteerabilityItem
from lbe.io.jsonl import read_jsonl, write_jsonl


def run_v2_item(
    item: SteerabilityItem,
    model: Any,
    model_name: str,
    max_new_tokens: int,
    seed: int | None = None,
) -> EvalResult:
    """Generate base and steered responses for one item. Scoring deferred.

    Args:
        item: The item to run.
        model: A Model backend.
        model_name: Loader identifier, recorded on the result.
        max_new_tokens: Visible-answer token budget. Reasoning-capable
            backends add their own internal buffer on top of this.
        seed: Recorded on the result for schema compatibility only. It is
            NOT forwarded to the backend — the Model interface excludes
            sampling controls because most provider APIs reject them for
            reasoning models (see base.py). Defaults to None rather than 42
            so new records do not misleadingly claim a seed was applied.

    Returns:
        EvalResult with raw_completions=[base, steered] and finish_reasons
        in the same order, so downstream code can tell a short answer apart
        from an answer truncated at the token ceiling.
    """
    base = model.generate(item.base_prompt, max_new_tokens=max_new_tokens)
    steered = model.generate(item.steering_instruction, max_new_tokens=max_new_tokens)
    return EvalResult(
        item_id=item.id,
        item_type=item.item_type,
        model_name=model_name,
        seed=seed,
        raw_completions=[base.text, steered.text],
        finish_reasons=[base.finish_reason, steered.finish_reason],
        score=None,
        extra={"category": item.category},
    )


def run_v2_eval(
    items_path: Path,
    model: Any,
    model_name: str,
    output_path: Path,
    max_new_tokens: int = 500,
    seed: int | None = None,
) -> None:
    """Run v2 eval across all items in items_path, write to output_path.

    Prints a truncation summary at the end: any nonzero count here means
    those responses were cut off at the token ceiling and should be re-run
    with a larger --max-tokens before being judged, since a truncated
    response can be misclassified (e.g. a response cut off before its
    values caveat looks like clean compliance).
    """
    items = list(read_jsonl(items_path, SteerabilityItem))
    print(f"Loaded {len(items)} items from {items_path.name}")

    results: list[EvalResult] = []
    for i, item in enumerate(items, 1):
        result = run_v2_item(
            item,
            model,
            model_name=model_name,
            max_new_tokens=max_new_tokens,
            seed=seed,
        )
        results.append(result)
        if i % 10 == 0 or i == len(items):
            print(f"  Progress: {i}/{len(items)}")

    write_jsonl(output_path, results)
    print(f"Wrote {len(results)} results to {output_path.name}")

    truncated = [
        (r.item_id, cond)
        for r in results
        for cond, reason in zip(("base", "steered"), r.finish_reasons or [], strict=False)
        if reason in ("length", "max_tokens")
    ]
    if truncated:
        print(
            f"\nWARNING: {len(truncated)} response(s) hit the token ceiling "
            f"and are truncated mid-generation:"
        )
        for item_id, cond in truncated:
            print(f"  {item_id} [{cond}]")
        print(
            "Re-run these with a larger --max-tokens before judging. "
            "See scripts/find_truncated.py."
        )
    else:
        print("\nNo truncated responses: all generations ended naturally.")
