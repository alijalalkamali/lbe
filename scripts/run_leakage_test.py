"""Run the judge-prompt demand-characteristics control experiment.

See lbe.judging.leakage for the full rationale. In short: the judge prompt
tells the judge what the item is testing for, which may prime it toward the
expected label. This script re-judges a balanced sample twice — once with
the identical prompt (measuring the nondeterminism floor) and once with the
field removed — and compares.

Cost:
    216 triples x 2 arms = 432 judgments, roughly $6 at the project's
    observed per-judgment rate. Both arms are required; the stripped arm
    alone is uninterpretable because judges are nondeterministic.

Usage:
    # Sample and run both arms, then analyze
    python scripts/run_leakage_test.py

    # Resume a partially-completed run (skips triples already judged)
    python scripts/run_leakage_test.py

    # Analyze an existing run without calling any APIs
    python scripts/run_leakage_test.py --analyze-only

Writes:
    results/leakage/leakage_sample.csv       the frozen, seeded sample
    results/leakage/leakage_judgments.jsonl  raw output of both arms
    results/leakage/leakage_report.md        the analysis
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from pydantic import BaseModel

from lbe.io.dataset import EvalResult, SteerabilityItem
from lbe.io.jsonl import read_jsonl, write_jsonl
from lbe.judging.aggregate import load_all_judgments
from lbe.judging.judge_output import JudgeOutputError, parse_judge_output
from lbe.judging.judge_prompt import build_judge_prompt
from lbe.judging.leakage import (
    ARM_CONTROL,
    ARM_STRIPPED,
    analyze_leakage,
    format_leakage_report,
    sample_leakage_triples,
)
from lbe.judging.rubrics import get_rubric
from lbe.models.loader import load_model


class LeakageJudgment(BaseModel):
    """One re-judgment in one arm of the control experiment."""

    item_id: str
    category: str
    responder_model: str
    condition: str
    judge_model: str
    arm: str
    classification: str = ""
    original_classification: str = ""
    error: str = ""
    raw_output: str = ""


def sanitize_filename(name: str) -> str:
    """Mirror the sanitization used across the pipeline's file naming."""
    return name.replace(":", "_").replace("/", "_")


def _key(row) -> tuple:
    return (
        row["item_id"],
        row["responder_model"],
        row["condition"],
        row["judge_model"],
        row["arm"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Two-arm control experiment for judge-prompt priming."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Sampling seed. Fixed by default so the sample is reproducible.",
    )
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Skip judging; analyze whatever is already in leakage_judgments.jsonl.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=800,
        help="Judge response budget. Default 800, matching run_judges.py.",
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
    out_dir = results_dir / "leakage"
    out_dir.mkdir(parents=True, exist_ok=True)

    sample_path = out_dir / "leakage_sample.csv"
    judgments_path = out_dir / "leakage_judgments.jsonl"
    report_path = out_dir / "leakage_report.md"

    if not args.analyze_only:
        if not items_path.exists():
            sys.exit(f"Items file not found: {items_path}")

        # Reuse the frozen sample if one exists, so a resumed run judges the
        # same triples rather than silently drawing a new sample.
        if sample_path.exists():
            sample = pd.read_csv(sample_path)
            print(f"Reusing existing sample: {len(sample)} triples " f"({sample_path.name})")
        else:
            print("Loading main-study judgments to draw the sample...")
            judgments = load_all_judgments(judgments_dir)
            sample = sample_leakage_triples(judgments, seed=args.seed)
            sample.to_csv(sample_path, index=False)
            print(f"Drew {len(sample)} triples -> {sample_path.name}")

        items = {i.id: i for i in read_jsonl(items_path, SteerabilityItem)}

        # Cache responder result files; each is read once, not per triple.
        responder_cache: dict[str, dict[str, EvalResult]] = {}

        def responses_for(responder: str) -> dict[str, EvalResult]:
            if responder not in responder_cache:
                path = results_dir / f"steerability_v2_{sanitize_filename(responder)}.jsonl"
                if not path.exists():
                    sys.exit(f"Responder results not found: {path}")
                responder_cache[responder] = {r.item_id: r for r in read_jsonl(path, EvalResult)}
            return responder_cache[responder]

        existing: list[LeakageJudgment] = (
            list(read_jsonl(judgments_path, LeakageJudgment)) if judgments_path.exists() else []
        )
        done = {(r.item_id, r.responder_model, r.condition, r.judge_model, r.arm) for r in existing}
        if existing:
            print(f"Resuming: {len(existing)} judgment(s) already done")

        # Build the full work list across both arms before judging, so the
        # per-judge model is loaded once rather than once per triple.
        work: list[tuple] = []
        for _, row in sample.iterrows():
            for arm in (ARM_CONTROL, ARM_STRIPPED):
                k = (
                    row["item_id"],
                    row["responder_model"],
                    row["condition"],
                    row["judge_model"],
                    arm,
                )
                if k not in done:
                    work.append((row, arm))

        if not work:
            print("Both arms already complete. Nothing to judge.")
        else:
            print(f"To judge: {len(work)} (across {len(sample)} triples x 2 arms)")

        new_records: list[LeakageJudgment] = []
        judge_cache: dict = {}

        for idx, (row, arm) in enumerate(work, 1):
            judge_name = row["judge_model"]
            if judge_name not in judge_cache:
                judge_cache[judge_name] = load_model(judge_name)
            judge = judge_cache[judge_name]

            item = items[row["item_id"]]
            rubric = get_rubric(item.category)
            result = responses_for(row["responder_model"])[row["item_id"]]
            response_text = result.raw_completions[0 if row["condition"] == "base" else 1]

            prompt = build_judge_prompt(
                rubric=rubric,
                item_base_prompt=item.base_prompt,
                item_steering_instruction=item.steering_instruction,
                response_to_judge=response_text,
                condition=row["condition"],
                expected_behavior_change=item.expected_behavior_change,
                include_expected_behavior_change=(arm == ARM_CONTROL),
            )

            record = LeakageJudgment(
                item_id=row["item_id"],
                category=row["category"],
                responder_model=row["responder_model"],
                condition=row["condition"],
                judge_model=judge_name,
                arm=arm,
                original_classification=row["original_classification"],
            )
            try:
                raw = judge.generate(prompt, max_new_tokens=args.max_tokens).text
                record.raw_output = raw
                try:
                    parsed = parse_judge_output(raw, rubric)
                    record.classification = parsed.classification
                except JudgeOutputError:
                    record.error = "parse_failed"
            except Exception as e:
                record.error = f"call_failed: {e!r}"

            new_records.append(record)

            if idx % 20 == 0 or idx == len(work):
                print(f"  [{idx}/{len(work)}]")
                write_jsonl(judgments_path, existing + new_records)

        write_jsonl(judgments_path, existing + new_records)
        print(f"Wrote {len(existing) + len(new_records)} judgments -> " f"{judgments_path.name}")

    if not judgments_path.exists():
        sys.exit(f"No judgments to analyze: {judgments_path} not found")

    records = list(read_jsonl(judgments_path, LeakageJudgment))
    df = pd.DataFrame([r.model_dump() for r in records])
    result = analyze_leakage(df)
    report = format_leakage_report(result)
    report_path.write_text(report, encoding="utf-8")

    print()
    print(report)
    print(f"Wrote report -> {report_path}")


if __name__ == "__main__":
    main()
