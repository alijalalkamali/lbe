"""Retry errored judgments for a judge across one or more responders.

Normal resumability in run_judges.py now only treats SUCCESSFUL judgments
as "already judged" -- rows left behind by a failed call are automatically
re-attempted on a plain pipeline re-run. This script remains useful for
explicitly targeting specific judge/responder pairs (rather than the whole
matrix) and for clearing stale .errors.jsonl files.

Fail-fast behavior:
    If a combination hits a fatal, section-wide condition (quota exhaustion,
    billing failure, invalid credentials, or a model access restriction),
    run_judge_on_responder raises FatalJudgeError immediately rather than
    grinding through every remaining item with an identical failure. This
    script catches that, prints a clean classified report (category, a
    plain-language summary, and -- where the provider supplied one -- the
    current time plus the estimated quota-reset time), and moves on to the
    next responder rather than crashing or hanging.

    Non-fatal, per-item errors (a single malformed response, a transient
    timeout) are unaffected -- those are still recorded per-item inside
    run_judge_on_responder and don't stop the run.

Usage:
    # Single responder (original usage still works)
    python scripts/retry_errors.py google:gemini-2.5-pro deepseek:deepseek-reasoner

    # Multiple responders in one call -- retries each in turn, printing a
    # clean report and moving on if one hits a fatal condition
    python scripts/retry_errors.py google:gemini-2.5-pro \\
        deepseek:deepseek-reasoner openai:gpt-5 anthropic:claude-opus-4-7 \\
        together:meta-llama/Llama-3.3-70B-Instruct-Turbo

    python scripts/retry_errors.py google:gemini-2.5-pro \\
        together:meta-llama/Llama-3.3-70B-Instruct-Turbo --sleep 90
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Reuse the exact same path-construction helpers the main pipeline uses,
# so filenames are guaranteed to match -- do not reimplement the slug logic.
from run_judge_pipeline import judge_output_path, responder_results_path

from lbe.io.jsonl import read_jsonl, write_jsonl
from lbe.judging.run_judges import FatalJudgeError, JudgmentRecord, run_judge_on_responder
from lbe.models.error_utils import format_error_report


def strip_errors(output_path: Path) -> int:
    """Remove error-populated records from a judge output file in place.

    Args:
        output_path: Path to the judge's main JSONL output file.

    Returns:
        Number of records removed.
    """
    if not output_path.exists():
        return 0
    records = list(read_jsonl(output_path, JudgmentRecord))
    good = [r for r in records if not r.error]
    n_removed = len(records) - len(good)
    write_jsonl(output_path, good)
    return n_removed


def retry_one(
    judge_model: str,
    responder_model: str,
    items_path: Path,
    results_dir: Path,
    sleep_before: float,
) -> bool:
    """Retry one judge/responder combination.

    Returns:
        True if the combination completed without a fatal error (it may
        still have per-item errors -- those are non-fatal and expected
        to be retried again another time). False if a fatal condition
        aborted it.
    """
    rp = responder_results_path(results_dir, responder_model)
    if not rp.exists():
        print(f"  Responder result file not found: {rp} -- skipping.")
        return True  # not a fatal API condition, just nothing to do

    output_path = judge_output_path(results_dir, judge_model, responder_model)
    error_log_path = output_path.with_suffix(".errors.jsonl")

    n_removed = strip_errors(output_path)
    print(f"  Removed {n_removed} errored record(s) from {output_path.name}.")

    if error_log_path.exists():
        error_log_path.unlink()
        print(f"  Cleared stale {error_log_path.name}.")

    if n_removed == 0:
        print("  Nothing to retry.")
        return True

    if sleep_before > 0:
        print(f"  Waiting {sleep_before:.0f}s before retrying (rate-limit cooldown)...")
        time.sleep(sleep_before)

    try:
        run_judge_on_responder(
            judge_model_name=judge_model,
            responder_model_name=responder_model,
            items_path=items_path,
            responder_results_path=rp,
            output_path=output_path,
            error_log_path=error_log_path,
        )
    except FatalJudgeError as e:
        context = f"judge={judge_model} responder={responder_model}"
        print()
        print(format_error_report(e, context=context))
        print("  Aborting this combination; moving on.")
        return False

    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Retry errored judgments for a judge across one or more responders."
    )
    parser.add_argument("judge_model", help="e.g. google:gemini-2.5-pro")
    parser.add_argument(
        "responder_models",
        nargs="+",
        help="One or more responder models, e.g. "
        "deepseek:deepseek-reasoner openai:gpt-5. Each is retried in turn; "
        "a fatal error (quota/billing/access) on one does not stop the rest.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.0,
        help="Seconds to wait before EACH retry -- use this if the errors "
        "were rate-limit related, to let the provider's quota window "
        "reset before hammering the same limit again. Applied once per "
        "responder, before that responder's retry begins.",
    )
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
        sys.exit(f"Items file not found: {items_path}")

    print(f"Judge: {args.judge_model}")
    print(f"Responders queued: {len(args.responder_models)}")
    print()

    completed, aborted = [], []
    for i, responder in enumerate(args.responder_models, 1):
        print(f"[{i}/{len(args.responder_models)}] {args.judge_model} on {responder}")
        ok = retry_one(args.judge_model, responder, items_path, results_dir, args.sleep)
        (completed if ok else aborted).append(responder)
        print()

    print("=" * 70)
    print(f"Done. {len(completed)}/{len(args.responder_models)} completed without a fatal error.")
    if aborted:
        print(f"Aborted (fatal condition, needs attention before retrying): {aborted}")


if __name__ == "__main__":
    main()
