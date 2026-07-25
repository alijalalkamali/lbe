"""Re-run a v2 steerability eval on specific items and merge results.

Reads existing results, replaces entries for the selected items with fresh
runs, and writes the merged file back. Original results are backed up with a
.bak suffix before overwriting.

Items can be selected by explicit ID or by category. Category selection
exists because the common case — "regenerate every core-category item for
this model with a larger budget, because its responses were truncated" —
otherwise means pasting many IDs onto the command line.

Fail-fast behavior:
    This script generates for ONE model across potentially many items, so
    unlike the judge pipeline there's no "next combination" to move to --
    a fatal, section-wide error (quota exhaustion, billing failure, invalid
    credentials, model access restriction) means every remaining item for
    THIS model will fail identically. Rather than crash uninformatively or
    grind through each remaining item hitting the same wall, this script:
      1. Prints one clean, classified error report (category, plain-language
         summary, current time, and the provider's estimated retry-after
         time if one was supplied) instead of a raw exception dump.
      2. Stops generating further items immediately.
      3. Writes a merged results file containing whatever succeeded before
         the abort, so no completed work is lost.
      4. Reports exactly which items still need to be run, so you can
         re-invoke this script for just those once the underlying issue
         (quota reset, billing top-up, wrong project) is resolved.

    A non-fatal, per-item error (a single transient timeout, a one-off
    content-filter block) is recorded and the run continues to the next
    item -- only a fatal, section-wide condition stops the run early.

IMPORTANT — regenerating a response invalidates its judgments:
    run_judge_pipeline.py is resumable and will NOT re-judge an item it has
    already judged, so after this script runs, the old judgments still sit
    in the judge files describing a response that no longer exists. Clear
    them first, or the analysis silently pairs new responses with stale
    labels:

        python scripts/invalidate_judgments.py --responder <model> \\
            --categories <same categories> --yes
        python scripts/run_judge_pipeline.py --responders <model>

Usage:
    # Explicit item IDs
    python scripts/rerun_items.py openai:gpt-5 --item-ids sty_002 rvs_014

    # Whole categories, larger budget (the truncation-repair case)
    python scripts/rerun_items.py together:Qwen/Qwen3.7-Max \\
        --categories values_conflict_low reasoning_values_elicit reasoning_values_suppress \\
        --max-tokens 1500

Reads:
    data/<items-file> (default: steerability_items_v2.jsonl)
    results/steerability_v2_<sanitized_model>.jsonl

Writes:
    results/steerability_v2_<sanitized_model>.jsonl (merged)
    results/steerability_v2_<sanitized_model>.jsonl.bak (backup)
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from lbe.evals.steerability_v2 import run_v2_item
from lbe.io.dataset import EvalResult, SteerabilityItem
from lbe.io.jsonl import read_jsonl, write_jsonl
from lbe.models.base import TRUNCATION_FINISH_REASONS
from lbe.models.error_utils import classify_error, format_error_report
from lbe.models.loader import load_model


def sanitize_filename(name: str) -> str:
    """Replace filesystem-unfriendly characters in model names.

    Mirrors the sanitization used by run_v2_local.py so both scripts read
    and write the same result file paths.
    """
    return name.replace(":", "_").replace("/", "_")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Re-run specific v2 items on a model and merge into existing results."
    )
    parser.add_argument("model", help="Model identifier passed to load_model().")
    parser.add_argument(
        "--item-ids",
        nargs="*",
        default=None,
        help="Item IDs to re-run (e.g., sty_002 rvs_014). Mutually exclusive " "with --categories.",
    )
    parser.add_argument(
        "--categories",
        nargs="*",
        default=None,
        help="Re-run every item in these categories. Mutually exclusive with --item-ids.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=500,
        help="Max visible tokens per response. Default 500. Raise this when "
        "repairing truncated responses.",
    )
    parser.add_argument(
        "--items-file",
        default="steerability_items_v2.jsonl",
        help="Items file under data/ to read from. Default: steerability_items_v2.jsonl. "
        "Use steerability_items_v3.jsonl when working with the expanded item set.",
    )
    args = parser.parse_args()

    if bool(args.item_ids) == bool(args.categories):
        sys.exit("Provide exactly one of --item-ids or --categories.")

    repo_root = Path(__file__).resolve().parent.parent
    items_path = repo_root / "data" / args.items_file
    results_dir = repo_root / "results"

    safe_name = sanitize_filename(args.model)
    results_path = results_dir / f"steerability_v2_{safe_name}.jsonl"

    if not items_path.exists():
        sys.exit(f"Items file not found: {items_path}")
    if not results_path.exists():
        sys.exit(
            f"Results file not found: {results_path}\n"
            f"Cannot merge into a nonexistent file. Run the full eval first."
        )

    # Load current results and index by item_id for O(1) replacement.
    existing_results = list(read_jsonl(results_path, EvalResult))
    results_by_id: dict[str, EvalResult] = {r.item_id: r for r in existing_results}

    # Load items and resolve the selection to a concrete ID list.
    all_items = {i.id: i for i in read_jsonl(items_path, SteerabilityItem)}

    if args.categories:
        known_categories = {i.category for i in all_items.values()}
        unknown = set(args.categories) - known_categories
        if unknown:
            sys.exit(f"Unknown categories: {sorted(unknown)}. Known: {sorted(known_categories)}")
        item_ids = sorted(i.id for i in all_items.values() if i.category in args.categories)
        print(f"Selected {len(item_ids)} item(s) from categories {args.categories}")
    else:
        item_ids = list(args.item_ids)
        missing_from_dataset = [i for i in item_ids if i not in all_items]
        if missing_from_dataset:
            sys.exit(f"These item IDs are not in {items_path.name}: {missing_from_dataset}")

    missing_from_results = [i for i in item_ids if i not in results_by_id]
    if missing_from_results:
        # Not fatal — could be a legitimate case (never ran these items).
        # But surface it so the user knows what's happening.
        print(
            f"Note: {len(missing_from_results)} item(s) not in existing results, "
            f"will be added: {missing_from_results}"
        )

    # Backup the existing results file before any modification.
    backup_path = results_path.with_suffix(results_path.suffix + ".bak")
    shutil.copy2(results_path, backup_path)
    print(f"Backed up existing results to {backup_path.name}")

    print(f"Model: {args.model}")
    print(f"max_new_tokens: {args.max_tokens}")
    print(f"Re-running {len(item_ids)} item(s)")

    # Load model and re-run the selected items.
    model = load_model(args.model)
    still_truncated: list[tuple[str, str]] = []
    succeeded_ids: list[str] = []
    not_attempted_ids: list[str] = []
    aborted_early = False

    for i, item_id in enumerate(item_ids, 1):
        item = all_items[item_id]
        print(f"  [{i}/{len(item_ids)}] {item_id}")

        try:
            new_result = run_v2_item(
                item=item,
                model=model,
                model_name=args.model,
                max_new_tokens=args.max_tokens,
            )
        except Exception as e:
            classified = classify_error(e)
            if classified.is_fatal:
                # Every remaining item will fail identically -- stop here,
                # save whatever succeeded, and report what's left rather
                # than grinding through the rest of item_ids.
                print()
                print(format_error_report(e, context=f"model={args.model} item={item_id}"))
                print(
                    f"  Fatal condition -- stopping. {len(succeeded_ids)}/{len(item_ids)} "
                    f"item(s) succeeded before this point."
                )
                not_attempted_ids = item_ids[i - 1 :]  # this one + everything after
                aborted_early = True
                break
            else:
                # Non-fatal, per-item failure: record and continue.
                print(f"    Non-fatal error, skipping this item: {classify_error(e).summary}")
                continue

        results_by_id[item_id] = new_result
        succeeded_ids.append(item_id)
        for cond, reason in zip(("base", "steered"), new_result.finish_reasons or [], strict=False):
            if reason in TRUNCATION_FINISH_REASONS:
                still_truncated.append((item_id, cond))

    # Reassemble preserving original ordering where possible.
    # For any new IDs not in the original file, append at the end.
    original_order = [r.item_id for r in existing_results]
    added_ids = [i for i in item_ids if i not in original_order and i in results_by_id]
    final_order = [i for i in original_order if i in results_by_id] + added_ids

    merged = [results_by_id[iid] for iid in final_order]

    write_jsonl(results_path, merged)
    print(f"\nWrote merged results ({len(merged)} items) to {results_path.name}")

    if aborted_early:
        print(
            f"\nRun stopped early due to a fatal error. "
            f"{len(succeeded_ids)}/{len(item_ids)} item(s) completed this run."
        )
        print("Still need to be run once the issue above is resolved:")
        print(f"  {not_attempted_ids}")
        if args.categories:
            print(
                f"\nRe-invoke with just the remaining items, e.g.:\n"
                f"  python scripts/rerun_items.py {args.model} "
                f"--item-ids {' '.join(not_attempted_ids)} --max-tokens {args.max_tokens} "
                f"--items-file {args.items_file}"
            )

    if still_truncated:
        print(
            f"\nWARNING: {len(still_truncated)} regenerated response(s) are "
            f"STILL truncated at --max-tokens={args.max_tokens}:"
        )
        for item_id, cond in still_truncated:
            print(f"  {item_id} [{cond}]")
        print("Raise --max-tokens and re-run these before judging.")
    elif succeeded_ids:
        print("\nAll regenerated responses this run ended naturally (no truncation).")

    if succeeded_ids:
        if args.categories:
            scope_flag = "--categories " + " ".join(args.categories)
        else:
            scope_flag = "--item-ids " + " ".join(succeeded_ids)

        print(
            f"\nIMPORTANT: judgments for these items are now stale. Clear and "
            f"refill them:\n"
            f"  python scripts/invalidate_judgments.py --responder {args.model} "
            f"{scope_flag} --yes\n"
            f"  python scripts/run_judge_pipeline.py --responders {args.model}"
        )


if __name__ == "__main__":
    main()
