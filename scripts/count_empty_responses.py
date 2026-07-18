"""Count empty base/steered responses in a v2 steerability results file.

Reads results/steerability_v2_<model>.jsonl and reports:
  - Total items
  - Items with empty base response
  - Items with empty steered response
  - Items with both empty
  - Item IDs for each empty case (for targeted re-runs)

Usage:
    python scripts/count_empty_responses.py results/steerability_v2_openai_gpt-5.jsonl

Empty defined as: raw_completions[i] is None, empty string, or whitespace-only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lbe.io.dataset import EvalResult
from lbe.io.jsonl import read_jsonl


def is_empty(text: str | None) -> bool:
    """Return True if the response has no meaningful content."""
    return text is None or not text.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Count empty responses in a v2 results file.")
    parser.add_argument(
        "results_path",
        type=Path,
        help="Path to results/steerability_v2_<model>.jsonl",
    )
    args = parser.parse_args()

    if not args.results_path.exists():
        sys.exit(f"File not found: {args.results_path}")

    results = list(read_jsonl(args.results_path, EvalResult))
    total = len(results)

    empty_base_ids: list[str] = []
    empty_steered_ids: list[str] = []
    both_empty_ids: list[str] = []

    for r in results:
        # v2 results store [base, steered] in raw_completions
        base = r.raw_completions[0] if len(r.raw_completions) > 0 else None
        steered = r.raw_completions[1] if len(r.raw_completions) > 1 else None

        base_empty = is_empty(base)
        steered_empty = is_empty(steered)

        if base_empty:
            empty_base_ids.append(r.item_id)
        if steered_empty:
            empty_steered_ids.append(r.item_id)
        if base_empty and steered_empty:
            both_empty_ids.append(r.item_id)

    print(f"File: {args.results_path.name}")
    print(f"Total items: {total}")
    print()
    print(f"Empty base responses:    {len(empty_base_ids):3d} / {total}")
    print(f"Empty steered responses: {len(empty_steered_ids):3d} / {total}")
    print(f"Both empty:              {len(both_empty_ids):3d} / {total}")
    print()

    if empty_base_ids:
        print(f"Items with empty base ({len(empty_base_ids)}):")
        for iid in empty_base_ids:
            print(f"  {iid}")
        print()

    if empty_steered_ids:
        print(f"Items with empty steered ({len(empty_steered_ids)}):")
        for iid in empty_steered_ids:
            print(f"  {iid}")
        print()

    # Union of all affected items — the set that would need re-running.
    affected = sorted(set(empty_base_ids) | set(empty_steered_ids))
    if affected:
        print(f"Total unique items affected (union): {len(affected)}")
        print("Item IDs (for targeted re-run):")
        for iid in affected:
            print(f"  {iid}")


if __name__ == "__main__":
    main()
