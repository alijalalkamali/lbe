"""Invalidate judgments for specific (responder, item, condition) triples.

Why this exists:
    run_judges.py is resumable by design: it skips any (item_id, condition)
    key already present in a judge's output file. That is correct for
    crash-recovery, but it means a regenerated response is NEVER re-judged —
    the pipeline sees the old judgment and moves on, silently pairing a new
    response with a stale label.

    This script deletes the affected rows from every judge's output file for
    a given responder. The next run_judge_pipeline.py invocation then sees
    those keys as missing and re-judges them against the regenerated
    responses, with no change needed to the pipeline itself.

    This is the same mechanism as scripts/retry_errors.py (which frees up
    errored rows); kept separate because the selection criterion is
    different — "the response underneath changed" rather than "the judgment
    failed to parse".

Safety:
    Every modified file is backed up to <name>.jsonl.bak before writing.
    Nothing is deleted without --yes, and a dry run is the default so you
    can see the blast radius first.

Usage:
    # Dry run: show what would be invalidated
    python scripts/invalidate_judgments.py \\
        --responder together:Qwen/Qwen3.7-Max \\
        --categories values_conflict_low reasoning_values_elicit reasoning_values_suppress

    # Actually do it
    python scripts/invalidate_judgments.py \\
        --responder together:Qwen/Qwen3.7-Max \\
        --categories values_conflict_low reasoning_values_elicit reasoning_values_suppress \\
        --yes

    # Specific items only
    python scripts/invalidate_judgments.py \\
        --responder together:meta-llama/Llama-3.3-70B-Instruct-Turbo \\
        --item-ids rve_002 rvs_005 --yes

Then re-judge:
    python scripts/run_judge_pipeline.py --responders <responder>
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from lbe.io.jsonl import read_jsonl, write_jsonl
from lbe.judging.run_judges import JudgmentRecord


def sanitize_filename(name: str) -> str:
    """Mirror the sanitization used across the pipeline's file naming."""
    return name.replace(":", "_").replace("/", "_")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delete judgments for a responder so they get re-judged."
    )
    parser.add_argument(
        "--responder",
        required=True,
        help="Responder model whose judgments should be invalidated.",
    )
    parser.add_argument(
        "--categories",
        nargs="*",
        default=None,
        help="Invalidate only these categories. Mutually exclusive with "
        "--item-ids. If neither is given, ALL of this responder's "
        "judgments are invalidated.",
    )
    parser.add_argument(
        "--item-ids",
        nargs="*",
        default=None,
        help="Invalidate only these item IDs. Mutually exclusive with " "--categories.",
    )
    parser.add_argument(
        "--conditions",
        nargs="*",
        default=["base", "steered"],
        choices=["base", "steered"],
        help="Which conditions to invalidate. Default: both.",
    )
    parser.add_argument(
        "--judgments-dir",
        type=Path,
        default=None,
        help="Directory of judge_*.jsonl files. Default: <repo>/results/judgments",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Actually modify files. Without this, performs a dry run.",
    )
    args = parser.parse_args()

    if args.categories and args.item_ids:
        sys.exit("--categories and --item-ids are mutually exclusive.")

    repo_root = Path(__file__).resolve().parent.parent
    judgments_dir = args.judgments_dir or (repo_root / "results" / "judgments")
    if not judgments_dir.is_dir():
        sys.exit(f"Judgments directory not found: {judgments_dir}")

    safe_responder = sanitize_filename(args.responder)
    # Judge files are named judge_<judge>_on_<responder>.jsonl — match the
    # responder suffix so all six judges' files for this responder are found.
    pattern = f"judge_*_on_{safe_responder}.jsonl"
    paths = sorted(judgments_dir.glob(pattern))
    if not paths:
        sys.exit(
            f"No judge files matched {pattern!r} in {judgments_dir}.\n"
            f"Check the responder identifier spelling."
        )

    print(f"Responder: {args.responder}")
    print(f"Matched {len(paths)} judge file(s)")
    if args.categories:
        print(f"Scope: categories={args.categories}")
    elif args.item_ids:
        print(f"Scope: item_ids={args.item_ids}")
    else:
        print("Scope: ALL items for this responder")
    print(f"Conditions: {args.conditions}")
    print(f"Mode: {'APPLY' if args.yes else 'DRY RUN (use --yes to apply)'}")
    print()

    def should_invalidate(record: JudgmentRecord) -> bool:
        if record.condition not in args.conditions:
            return False
        if args.categories is not None:
            return record.category in args.categories
        if args.item_ids is not None:
            return record.item_id in args.item_ids
        return True

    total_removed = 0
    for path in paths:
        records = list(read_jsonl(path, JudgmentRecord))
        keep = [r for r in records if not should_invalidate(r)]
        removed = len(records) - len(keep)
        total_removed += removed

        print(f"  {path.name}: {len(records)} -> {len(keep)} ({removed} invalidated)")

        if removed and args.yes:
            backup = path.with_suffix(path.suffix + ".bak")
            shutil.copy2(path, backup)
            write_jsonl(path, keep)

    print()
    if not args.yes:
        print(
            f"DRY RUN — nothing written. {total_removed} judgment(s) would be "
            f"invalidated. Re-run with --yes to apply."
        )
        return

    print(f"Invalidated {total_removed} judgment(s). Backups written as *.jsonl.bak")
    print(
        f"\nNext step — refill them:\n"
        f"  python scripts/run_judge_pipeline.py --responders {args.responder}"
    )


if __name__ == "__main__":
    main()
