"""Retry errored judgments for one judge-responder combination.

Normal resumability in run_judges.py treats any existing (item_id,
condition) key in the output file as "already judged" -- including rows
where classification failed and `error` is populated. Rerunning
run_judge_pipeline.py will therefore skip errored judgments forever
rather than retry them.

This script fixes that: it strips error-populated rows out of the main
output file, deletes the stale .errors.jsonl, and re-invokes
run_judge_on_responder so only the now-missing keys get re-attempted.

Usage:
    python scripts/retry_errors.py google:gemini-2.5-pro google:gemini-2.5-pro
    python scripts/retry_errors.py google:gemini-2.5-pro \
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
from lbe.judging.run_judges import JudgmentRecord, run_judge_on_responder


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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Retry errored judgments for one judge-responder pair."
    )
    parser.add_argument("judge_model", help="e.g. google:gemini-2.5-pro")
    parser.add_argument("responder_model", help="e.g. google:gemini-2.5-pro")
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.0,
        help="Seconds to wait before retrying -- use this if the errors "
        "were rate-limit related, to let the provider's quota window "
        "reset before hammering the same limit again.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    items_path = repo_root / "data" / "steerability_items_v2.jsonl"
    results_dir = repo_root / "results"

    rp = responder_results_path(results_dir, args.responder_model)
    if not rp.exists():
        sys.exit(f"Responder result file not found: {rp}")

    output_path = judge_output_path(results_dir, args.judge_model, args.responder_model)
    error_log_path = output_path.with_suffix(".errors.jsonl")

    n_removed = strip_errors(output_path)
    print(f"Removed {n_removed} errored record(s) from {output_path.name}.")

    if error_log_path.exists():
        error_log_path.unlink()
        print(f"Cleared stale {error_log_path.name}.")

    if n_removed == 0:
        print("Nothing to retry.")
        return

    if args.sleep > 0:
        print(f"Waiting {args.sleep:.0f}s before retrying (rate-limit cooldown)...")
        time.sleep(args.sleep)

    run_judge_on_responder(
        judge_model_name=args.judge_model,
        responder_model_name=args.responder_model,
        items_path=items_path,
        responder_results_path=rp,
        output_path=output_path,
        error_log_path=error_log_path,
    )


if __name__ == "__main__":
    main()
