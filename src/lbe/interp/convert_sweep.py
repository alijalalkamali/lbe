"""
Convert an activation-steering sweep output into per-alpha EvalResult files
that the existing judge pipeline can consume.

Each (layer, alpha) arm becomes its own pseudo-model result file:

    results/steerability_v2_steered_L{layer}_alpha{+a}.jsonl

with model_name "steered:L{layer}:alpha{+a}" and the steered-sweep generation
in raw_completions[0] (the BASE slot -- these are generations on base
prompts; the intervention lives in activation space, not in the prompt).
raw_completions[1] is left as an empty string placeholder.

OPEN ASSUMPTION (confirm against run_judges.py before judging): the judge
runner tolerates an empty steered-condition completion, or can be pointed at
the base condition only. If it iterates both conditions unconditionally,
judge only the base condition for these files, or the empty slot will
produce junk judgments that must be excluded downstream.

Usage:
    python -m lbe.interp.convert_sweep \
        --sweep-path results/interp/steering_sweep_L40.jsonl \
        --output-dir results/
"""

from __future__ import annotations

import argparse
import json
import logging
from collections import defaultdict
from pathlib import Path

from lbe.io.dataset import EvalResult
from lbe.io.jsonl import write_jsonl

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _alpha_tag(alpha: float) -> str:
    """+3, -6, +0 ... stable, filesystem-safe, sign always explicit."""
    return f"{alpha:+g}"


def convert_sweep(sweep_path: Path, output_dir: Path) -> list[Path]:
    if not sweep_path.exists():
        raise FileNotFoundError(f"Sweep file not found: {sweep_path}")

    by_arm: dict[tuple[int, float], list[dict]] = defaultdict(list)
    with sweep_path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"{sweep_path}:{line_num}: invalid JSON: {e}") from e
            required = {
                "item_id",
                "category",
                "layer_index",
                "alpha",
                "completion",
                "finish_reason",
            }
            missing = required - set(rec)
            if missing:
                raise ValueError(f"{sweep_path}:{line_num}: missing fields {sorted(missing)}")
            by_arm[(rec["layer_index"], rec["alpha"])].append(rec)

    if not by_arm:
        raise ValueError(f"No records found in {sweep_path}")

    # Same item set in every arm, no duplicates within an arm.
    item_sets = {arm: {r["item_id"] for r in recs} for arm, recs in by_arm.items()}
    reference = next(iter(item_sets.values()))
    for arm, ids in item_sets.items():
        if len(ids) != len(by_arm[arm]):
            raise ValueError(f"Arm {arm}: duplicate item_ids present.")
        if ids != reference:
            raise ValueError(
                f"Arm {arm} covers a different item set than other arms "
                f"(symmetric difference: {sorted(ids ^ reference)[:5]}...). "
                f"An incomplete sweep should be completed or the arm dropped, "
                f"not converted silently."
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for (layer, alpha), recs in sorted(by_arm.items()):
        tag = _alpha_tag(alpha)
        model_name = f"steered:L{layer}:alpha{tag}"
        results = [
            EvalResult(
                item_id=r["item_id"],
                item_type="steerability",
                model_name=model_name,
                seed=None,
                raw_completions=[r["completion"], ""],
                finish_reasons=[r["finish_reason"], None],
                score=None,
                extra={
                    "category": r["category"],
                    "steering_layer": layer,
                    "steering_alpha": alpha,
                    "source_sweep": str(sweep_path),
                },
            )
            for r in sorted(recs, key=lambda r: r["item_id"])
        ]
        out_path = output_dir / f"steerability_v2_steered_L{layer}_alpha{tag}.jsonl"
        write_jsonl(out_path, results)
        n_len = sum(1 for r in recs if r["finish_reason"] == "length")
        logger.info(
            "%s: %d items -> %s (%d hit the token ceiling)",
            model_name,
            len(results),
            out_path,
            n_len,
        )
        written.append(out_path)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sweep-path", required=True, type=Path)
    parser.add_argument("--output-dir", default=Path("results"), type=Path)
    args = parser.parse_args()
    convert_sweep(args.sweep_path, args.output_dir)


if __name__ == "__main__":
    main()
