"""Top-level judge pipeline runner.

Runs a set of judge models across a set of responder models' result files,
producing per-judge JSONL outputs and (optionally) an aggregated analysis
CSV.

Usage:
    # Run all judges on all responders (long run, hours)
    python scripts/run_judge_pipeline.py

    # Run a single judge on a single responder (for testing)
    python scripts/run_judge_pipeline.py \\
        --judges anthropic:claude-sonnet-4-6 \\
        --responders anthropic:claude-haiku-4-5

    # Aggregate only (after judgments are complete)
    python scripts/run_judge_pipeline.py --aggregate-only

Judge and responder identifiers use the same 'provider:model' strings that
loader.py understands.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lbe.judging.aggregate import (
    compute_consensus,
    compute_judge_divergence,
    compute_pairwise_agreement,
    load_all_judgments,
    save_analysis_ready_csv,
)
from lbe.judging.run_judges import run_judge_on_responder

# Default set of judges and responders used when --judges / --responders
# are not passed. One frontier model per lab (6 total) — Haiku 4.5 is
# collected on disk but excluded from analysis to keep the methodology
# symmetric across labs.
DEFAULT_MODELS = [
    "anthropic:claude-opus-4-7",
    "openai:gpt-5",
    "deepseek:deepseek-reasoner",
    "together:Qwen/Qwen3.7-Max",
    "together:meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "google:gemini-2.5-pro",
]


def sanitize_filename(name: str) -> str:
    """Replace filesystem-unfriendly characters."""
    return name.replace(":", "_").replace("/", "_")


def judge_output_path(results_dir: Path, judge_model: str, responder_model: str) -> Path:
    """Construct the per-(judge, responder) output path."""
    return (
        results_dir
        / "judgments"
        / (
            f"judge_{sanitize_filename(judge_model)}"
            f"_on_{sanitize_filename(responder_model)}.jsonl"
        )
    )


def responder_results_path(results_dir: Path, responder_model: str) -> Path:
    """Construct the path to a responder's v2 results file."""
    return results_dir / f"steerability_v2_{sanitize_filename(responder_model)}.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run LLM-judge pipeline across all judges × responders."
    )
    parser.add_argument(
        "--judges",
        nargs="*",
        default=None,
        help="Judge model identifiers (default: all 6 lab models).",
    )
    parser.add_argument(
        "--responders",
        nargs="*",
        default=None,
        help="Responder model identifiers (default: all 6 lab models).",
    )
    parser.add_argument(
        "--aggregate-only",
        action="store_true",
        help="Skip judging; only aggregate existing judgment files.",
    )
    parser.add_argument(
        "--skip-aggregate",
        action="store_true",
        help="Run judging but skip the aggregation step.",
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
    judgments_dir = results_dir / "judgments"

    if not items_path.exists():
        sys.exit(f"Items file not found: {items_path}")

    judges = args.judges if args.judges else DEFAULT_MODELS
    responders = args.responders if args.responders else DEFAULT_MODELS

    # Judgment phase
    if not args.aggregate_only:
        # Preflight: check all responder result files exist
        missing_responders = []
        for r in responders:
            rp = responder_results_path(results_dir, r)
            if not rp.exists():
                missing_responders.append((r, rp))
        if missing_responders:
            print("Missing responder result files:")
            for r, rp in missing_responders:
                print(f"  {r}: {rp}")
            sys.exit(1)

        total_combinations = len(judges) * len(responders)
        print(
            f"Running {len(judges)} judges on {len(responders)} responders "
            f"= {total_combinations} judge-responder combinations"
        )
        print(f"Judges: {judges}")
        print(f"Responders: {responders}")

        for judge_i, judge in enumerate(judges, 1):
            for responder_i, responder in enumerate(responders, 1):
                combo_i = (judge_i - 1) * len(responders) + responder_i
                print()
                print("=" * 70)
                print(f"[{combo_i}/{total_combinations}] " f"Judge={judge} Responder={responder}")
                print("=" * 70)

                output_path = judge_output_path(results_dir, judge, responder)
                error_log_path = output_path.with_suffix(".errors.jsonl")

                try:
                    run_judge_on_responder(
                        judge_model_name=judge,
                        responder_model_name=responder,
                        items_path=items_path,
                        responder_results_path=responder_results_path(results_dir, responder),
                        output_path=output_path,
                        error_log_path=error_log_path,
                    )
                except Exception as e:
                    # Log and continue — don't let one judge-responder
                    # combination kill the whole run
                    print(f"ERROR for judge={judge} responder={responder}: {e!r}")
                    continue

    # Aggregation phase
    if not args.skip_aggregate:
        if not judgments_dir.exists():
            print(f"No judgments directory at {judgments_dir}; skipping aggregate.")
            return
        print()
        print("=" * 70)
        print("AGGREGATION")
        print("=" * 70)

        df = load_all_judgments(judgments_dir)
        print(f"Loaded {len(df)} judgment records")

        consensus_df = compute_consensus(df)
        print(f"Computed consensus for {len(consensus_df)} response-conditions")

        save_analysis_ready_csv(consensus_df, judgments_dir / "aggregated_judgments.csv")

        pairwise_df = compute_pairwise_agreement(df)
        pairwise_df.to_csv(judgments_dir / "pairwise_agreement.csv", index=False)
        print("Wrote pairwise agreement to pairwise_agreement.csv")

        # Self-preference is measured as categorical divergence from
        # peer-judge consensus (leave-one-judge-out), not via an invented
        # favorable/unfavorable label scale. See compute_judge_divergence
        # docstring for the full rationale. Two outputs: a per-judge,
        # per-category mismatch-rate summary (magnitude), and a label-
        # substitution table restricted to mismatches (direction).
        divergence_summary_df, divergence_direction_df = compute_judge_divergence(df)
        divergence_summary_df.to_csv(judgments_dir / "judge_divergence_summary.csv", index=False)
        divergence_direction_df.to_csv(
            judgments_dir / "judge_divergence_direction.csv", index=False
        )
        print(
            "Wrote judge divergence summary and direction tables to "
            "judge_divergence_summary.csv / judge_divergence_direction.csv"
        )


if __name__ == "__main__":
    main()
