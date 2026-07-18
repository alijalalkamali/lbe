"""Report which responses were truncated at the token ceiling.

Why this exists:
    A response cut off mid-sentence because it exhausted its token budget is
    not evidence about the model's behavior — it is evidence about the
    budget. It is also silently misclassifiable: a response truncated before
    it reached its values caveat looks identical to clean compliance; one cut
    before its alternative suggestion looks like a flat refusal. Because
    rubric labels in this study distinguish exactly those multi-part
    structures, truncation is a direct threat to the validity of any
    "model X never does Y" claim.

    Response length alone cannot detect this — models legitimately differ in
    verbosity, and text-heuristics (does it end in punctuation?) produce
    heavy false positives on bullet lists and headers. The provider's
    finish_reason is the only reliable signal, so it is now recorded at
    generation time.

Backward compatibility:
    Result files written before finish_reasons existed have the field as
    null. Those rows are reported separately as UNKNOWN rather than counted
    as clean — absence of a recorded reason is not evidence of a clean stop.
    The only way to resolve UNKNOWN rows is to regenerate them.

Usage:
    # Report across every result file
    python scripts/find_truncated.py

    # One model, only the three core categories, IDs only (pipe to rerun)
    python scripts/find_truncated.py \\
        --model together:Qwen/Qwen3.7-Max \\
        --categories values_conflict_low reasoning_values_elicit reasoning_values_suppress \\
        --ids-only

Exit codes:
    0 — no truncated responses found in scope
    1 — truncated responses found (so this is usable as a CI/precommit gate)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lbe.io.dataset import EvalResult
from lbe.io.jsonl import read_jsonl
from lbe.models.base import TRUNCATION_FINISH_REASONS

CONDITIONS = ("base", "steered")


def sanitize_filename(name: str) -> str:
    """Mirror the sanitization used by run_v2_local.py / rerun_items.py."""
    return name.replace(":", "_").replace("/", "_")


def classify_result(
    result: EvalResult,
) -> list[tuple[str, str, str | None]]:
    """Return (condition, status, finish_reason) for each completion.

    status is one of:
        "truncated" — provider says it stopped at the token ceiling
        "clean"     — provider reported some other stop reason
        "unknown"   — no finish_reason recorded (pre-instrumentation record)
    """
    out: list[tuple[str, str, str | None]] = []
    reasons = result.finish_reasons or []
    for idx, condition in enumerate(CONDITIONS):
        if idx >= len(result.raw_completions):
            continue
        reason = reasons[idx] if idx < len(reasons) else None
        if reason is None:
            status = "unknown"
        elif reason in TRUNCATION_FINISH_REASONS:
            status = "truncated"
        else:
            status = "clean"
        out.append((condition, status, reason))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Report responses truncated at the token ceiling.")
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=None,
        help="Directory of steerability_v2_*.jsonl files. " "Default: <repo>/results",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Only inspect this model's result file. Default: all.",
    )
    parser.add_argument(
        "--categories",
        nargs="*",
        default=None,
        help="Only report items in these categories. Default: all.",
    )
    parser.add_argument(
        "--ids-only",
        action="store_true",
        help="Print only the affected item IDs, one per line, deduplicated "
        "across conditions. Intended to be piped into rerun_items.py.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    results_dir = args.results_dir or (repo_root / "results")
    if not results_dir.is_dir():
        sys.exit(f"Results directory not found: {results_dir}")

    if args.model:
        paths = [results_dir / f"steerability_v2_{sanitize_filename(args.model)}.jsonl"]
        if not paths[0].exists():
            sys.exit(f"Result file not found: {paths[0]}")
    else:
        paths = sorted(results_dir.glob("steerability_v2_*.jsonl"))
        if not paths:
            sys.exit(f"No steerability_v2_*.jsonl files in {results_dir}")

    any_truncated = False
    truncated_ids: set[str] = set()

    for path in paths:
        results = list(read_jsonl(path, EvalResult))
        rows = []
        n_clean = n_unknown = 0
        for result in results:
            category = result.extra.get("category")
            if args.categories and category not in args.categories:
                continue
            for condition, status, reason in classify_result(result):
                if status == "truncated":
                    rows.append((result.item_id, condition, reason, category))
                    truncated_ids.add(result.item_id)
                elif status == "unknown":
                    n_unknown += 1
                else:
                    n_clean += 1

        if rows:
            any_truncated = True

        if args.ids_only:
            continue

        print(f"=== {path.name} ===")
        print(
            f"  clean={n_clean}  truncated={len(rows)}  "
            f"unknown(no finish_reason recorded)={n_unknown}"
        )
        for item_id, condition, reason, category in rows:
            print(
                f"    TRUNCATED  {item_id} [{condition}]  "
                f"category={category}  finish_reason={reason!r}"
            )
        if n_unknown:
            print(
                f"  NOTE: {n_unknown} completion(s) predate finish_reason "
                f"recording. Their truncation status is unknown and cannot "
                f"be determined without regenerating them."
            )
        print()

    if args.ids_only:
        for item_id in sorted(truncated_ids):
            print(item_id)

    sys.exit(1 if any_truncated else 0)


if __name__ == "__main__":
    main()
