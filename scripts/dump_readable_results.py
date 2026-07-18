"""Dump steerability eval results to readable .txt files.

For each saved results file in `results/steerability*.jsonl`, produces a
matching `results/<model-slug>-readable.txt` that pairs each item's prompts
with the base and steered responses. Useful for close reading without
re-running the eval.

Usage:
    python scripts/dump_readable_results.py

Reads:
    data/steerability_items.jsonl
    results/steerability*.jsonl

Writes:
    results/<model-slug>-readable.txt for each results file found
"""

from __future__ import annotations

from pathlib import Path

from lbe.io.dataset import EvalResult, SteerabilityItem
from lbe.io.jsonl import read_jsonl


def dump_one(results_path: Path, items: dict[str, SteerabilityItem]) -> Path:
    """Write a readable .txt next to the results file. Returns the output path."""
    results = list(read_jsonl(results_path, EvalResult))

    # Derive a clean readable filename: steerability_qwen-... -> qwen-...-readable.txt
    stem = results_path.stem.removeprefix("steerability_")
    output_path = results_path.with_name(f"{stem}-readable.txt")

    with output_path.open("w", encoding="utf-8") as f:
        f.write(f"# Steerability eval results — {stem}\n")
        f.write(f"# Source: {results_path.name}\n")
        f.write(f"# Items: {len(results)}\n\n")

        for r in results:
            item = items.get(r.item_id)
            if item is None:
                # Defensive: results reference an item we don't have on disk
                f.write("=" * 80 + "\n")
                f.write(f"{r.item_id}: item not found in data/steerability_items.jsonl\n\n")
                continue

            category = r.extra.get("category", "?")
            score_str = f"{r.score:.1f}" if r.score is not None else "N/A"
            base_metric = r.extra.get("base_metric")
            steered_metric = r.extra.get("steered_metric")

            f.write("=" * 80 + "\n")
            f.write(f"{r.item_id}  category={category}  score={score_str}  ")
            f.write(f"base_metric={base_metric}  steered_metric={steered_metric}\n\n")

            f.write(f"BASE PROMPT:\n{item.base_prompt}\n\n")
            f.write(f"BASE RESPONSE:\n{r.raw_completions[0]}\n\n")
            f.write(f"STEERING INSTRUCTION:\n{item.steering_instruction}\n\n")
            f.write(f"STEERED RESPONSE:\n{r.raw_completions[1]}\n\n")

    return output_path


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    items_path = repo_root / "data" / "steerability_items.jsonl"
    results_dir = repo_root / "results"

    if not items_path.exists():
        raise FileNotFoundError(f"Items file not found: {items_path}")
    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    items = {i.id: i for i in read_jsonl(items_path, SteerabilityItem)}
    print(f"Loaded {len(items)} eval items from {items_path}")

    results_files = sorted(results_dir.glob("steerability*.jsonl"))
    if not results_files:
        print(f"No results files found in {results_dir}")
        return

    for results_path in results_files:
        out_path = dump_one(results_path, items)
        print(f"  {results_path.name} -> {out_path.name}")

    print(f"Wrote {len(results_files)} readable files to {results_dir}")


if __name__ == "__main__":
    main()
