"""Dump v2 steerability eval results to readable .txt files.

For each saved v2 results file in `results/steerability_v2_*.jsonl`, produces
a matching `results/<model-slug>-v2-readable.txt` that pairs each item's
prompts with the base and steered responses. Useful for close reading
without re-running the eval.

Usage:
    python scripts/dump_readable_v2.py
    python scripts/dump_readable_v2.py --items-file steerability_items_v3.jsonl

Reads:
    data/<items-file> (default: steerability_items_v2.jsonl)
    results/steerability_v2_*.jsonl

Writes:
    results/<model-slug>-v2-readable.txt for each results file found
"""

from __future__ import annotations

import argparse
from pathlib import Path

from lbe.io.dataset import EvalResult, SteerabilityItem
from lbe.io.jsonl import read_jsonl


def dump_one(results_path: Path, items: dict[str, SteerabilityItem]) -> Path:
    """Write a readable .txt next to the results file. Returns the output path.

    Item-not-found in the items file is handled defensively rather than
    crashing the whole dump — an unmatched result_id emits a marker block.
    """
    results = list(read_jsonl(results_path, EvalResult))

    # Derive filename: steerability_v2_<slug>.jsonl -> <slug>-v2-readable.txt
    stem = results_path.stem.removeprefix("steerability_v2_")
    output_path = results_path.with_name(f"{stem}-v2-readable.txt")

    with output_path.open("w", encoding="utf-8") as f:
        f.write(f"# Steerability v2 eval results — {stem}\n")
        f.write(f"# Source: {results_path.name}\n")
        f.write(f"# Items: {len(results)}\n\n")

        for r in results:
            item = items.get(r.item_id)
            category = r.extra.get("category", "?")

            f.write("=" * 80 + "\n")
            f.write(f"{r.item_id}  category={category}  model={r.model_name}\n\n")

            if item is None:
                f.write(f"[Item {r.item_id!r} not found in items file]\n\n")
                f.write(f"BASE RESPONSE:\n{r.raw_completions[0]}\n\n")
                f.write(f"STEERED RESPONSE:\n{r.raw_completions[1]}\n\n")
                continue

            f.write(f"BASE PROMPT:\n{item.base_prompt}\n\n")
            f.write(f"BASE RESPONSE:\n{r.raw_completions[0]}\n\n")
            f.write(f"STEERING INSTRUCTION:\n{item.steering_instruction}\n\n")
            f.write(f"STEERED RESPONSE:\n{r.raw_completions[1]}\n\n")
            f.write(f"EXPECTED BEHAVIOR CHANGE:\n{item.expected_behavior_change}\n\n")

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Dump v2 eval results to readable text.")
    parser.add_argument(
        "--items-file",
        default="steerability_items_v2.jsonl",
        help="Items file under data/. Use steerability_items_v3.jsonl for the expanded set.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    items_path = repo_root / "data" / args.items_file
    results_dir = repo_root / "results"

    if not items_path.exists():
        raise FileNotFoundError(f"Items file not found: {items_path}")
    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    items = {i.id: i for i in read_jsonl(items_path, SteerabilityItem)}
    print(f"Loaded {len(items)} items from {items_path}")

    results_files = sorted(results_dir.glob("steerability_v2_*.jsonl"))
    if not results_files:
        print(f"No v2 results files found in {results_dir}")
        return

    for results_path in results_files:
        out_path = dump_one(results_path, items)
        print(f"  {results_path.name} -> {out_path.name}")

    print(f"Wrote {len(results_files)} readable files to {results_dir}")


if __name__ == "__main__":
    main()
