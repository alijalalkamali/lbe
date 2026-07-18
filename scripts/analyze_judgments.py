"""Cross-lab analysis of judged steerability responses.

Reads the aggregated judgments CSV produced by run_judge_pipeline.py and
computes:
    - Per-category classification distributions by responder model
    - Pairwise Fisher's exact tests for lab differences on each classification
    - Bootstrap confidence intervals for rate differences
    - Fleiss' kappa per category (inter-judge agreement)
    - Effect sizes (Cohen's h) for proportion comparisons
    - FDR-adjusted p-values via Benjamini-Hochberg

Usage:
    python scripts/analyze_judgments.py

Reads:
    results/judgments/aggregated_judgments.csv
    results/judgments/pairwise_agreement.csv
    results/judgments/self_preference_bias.csv
    (all produced by run_judge_pipeline.py)

Writes:
    results/analysis/cross_lab_tables.csv
    results/analysis/statistical_tests.csv
    results/analysis/agreement_summary.txt
    results/analysis/analysis_report.md   (human-readable summary)

Rationale for each test:
    Fisher's exact: valid at any sample size; N=20/category is too small
        for chi-squared reliability.
    Bootstrap CIs: normal-approximation CIs unreliable at N=20; bootstrap
        is distribution-free.
    Cohen's h: standardized effect size for proportions. Report alongside
        p-values because effect size matters more than significance at
        small N.
    Benjamini-Hochberg: controls false discovery rate under multiple
        comparisons. Alpha=0.05 standard.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# =============================================================================
# Statistical primitives
# =============================================================================


def cohens_h(p1: float, p2: float) -> float:
    """Cohen's h effect size for two proportions.

    Range: 0 (no effect) to π (max effect). Conventions:
        - h ~ 0.2 = small effect
        - h ~ 0.5 = medium effect
        - h ~ 0.8 = large effect

    Handles edge cases where p1 or p2 is 0 or 1 by clamping.
    """
    # Clamp to avoid arcsin(sqrt(0)) or arcsin(sqrt(1)) numerical issues
    p1 = max(min(p1, 1.0 - 1e-9), 1e-9)
    p2 = max(min(p2, 1.0 - 1e-9), 1e-9)
    phi1 = 2 * math.asin(math.sqrt(p1))
    phi2 = 2 * math.asin(math.sqrt(p2))
    return abs(phi1 - phi2)


def bootstrap_rate_diff_ci(
    successes_a: int,
    total_a: int,
    successes_b: int,
    total_b: int,
    n_resamples: int = 10_000,
    alpha: float = 0.05,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Bootstrap CI for the difference in success rates between two groups.

    Returns:
        Tuple of (point_estimate, ci_lower, ci_upper) where the CI is
        (1-alpha) confidence, e.g. alpha=0.05 gives 95% CI.
    """
    if total_a == 0 or total_b == 0:
        return float("nan"), float("nan"), float("nan")

    rng = np.random.default_rng(seed)
    # Represent each group as a boolean array; resample with replacement
    a = np.concatenate([np.ones(successes_a), np.zeros(total_a - successes_a)])
    b = np.concatenate([np.ones(successes_b), np.zeros(total_b - successes_b)])

    diffs = np.empty(n_resamples)
    for i in range(n_resamples):
        sample_a = rng.choice(a, size=total_a, replace=True)
        sample_b = rng.choice(b, size=total_b, replace=True)
        diffs[i] = sample_a.mean() - sample_b.mean()

    point = successes_a / total_a - successes_b / total_b
    lo = float(np.percentile(diffs, 100 * alpha / 2))
    hi = float(np.percentile(diffs, 100 * (1 - alpha / 2)))
    return point, lo, hi


def benjamini_hochberg(pvalues: list[float], alpha: float = 0.05) -> list[float]:
    """Benjamini-Hochberg FDR-adjusted p-values.

    Returns a list of adjusted p-values in the same order as input.
    Adjusted p-values control the false discovery rate at level alpha.
    """
    n = len(pvalues)
    if n == 0:
        return []
    # Sort indices by p-value ascending
    order = sorted(range(n), key=lambda i: pvalues[i])
    ranked = [pvalues[i] for i in order]
    # Compute BH-adjusted p-values in sorted order, monotonically non-decreasing
    adjusted_sorted = [0.0] * n
    prev = 1.0
    for k_from_top in range(n, 0, -1):
        rank = k_from_top  # 1-indexed rank in sorted order
        raw = ranked[k_from_top - 1] * n / rank
        adjusted = min(prev, min(raw, 1.0))
        adjusted_sorted[k_from_top - 1] = adjusted
        prev = adjusted
    # Restore original order
    out = [0.0] * n
    for sorted_idx, orig_idx in enumerate(order):
        out[orig_idx] = adjusted_sorted[sorted_idx]
    return out


# =============================================================================
# Cross-lab tables
# =============================================================================


def build_classification_rate_table(
    aggregated_df: pd.DataFrame,
    consensus_column: str = "consensus_loo",
) -> pd.DataFrame:
    """Build per-(category, responder) rates of each classification label.

    Uses the leave-one-out consensus by default (excludes self-judgment).

    Args:
        aggregated_df: The aggregated_judgments.csv content, one row per
            (item_id, responder_model, condition).
        consensus_column: Which consensus column to use ('consensus' or
            'consensus_loo').

    Returns:
        Long-format DataFrame with columns:
            category, responder_model, condition, classification, count,
            total, rate.

        IMPORTANT: includes an explicit row (count=0, rate=0.0) for every
        (category, condition, responder_model) combination for every
        classification label that ANY responder produced within that same
        category/condition — not just labels that specific responder
        produced. Without this, a responder with a genuine 0/20 rate on a
        rare label has no row at all, which silently makes it impossible
        for downstream pairwise tests to compare it against models that
        did produce that label (there being no group member to pair with).
        This matters most for rare, lab-specific labels (e.g. a label only
        GPT-5 or only Opus produced) — exactly the comparisons a
        'some models do this, others never do' finding depends on.
    """
    rows = []
    grouped = aggregated_df.groupby(["category", "responder_model", "condition"])
    for (category, responder, condition), group in grouped:
        total = len(group)
        if total == 0:
            continue
        label_counts = group[consensus_column].value_counts()
        for label, count in label_counts.items():
            rows.append(
                {
                    "category": category,
                    "responder_model": responder,
                    "condition": condition,
                    "classification": label,
                    "count": int(count),
                    "total": int(total),
                    "rate": float(count) / total,
                }
            )
    result = pd.DataFrame(rows)

    # Backfill explicit zero-count rows: for every (category, condition),
    # every responder should have a row for every label ANY responder in
    # that category/condition produced.
    zero_rows = []
    for (category, condition), group in result.groupby(["category", "condition"]):
        all_labels = set(group["classification"].unique())
        all_responders = set(
            aggregated_df[(aggregated_df["category"] == category)]["responder_model"].unique()
        )
        existing = set(zip(group["responder_model"], group["classification"], strict=False))
        # total items for this responder/category/condition (same for all
        # responders in a symmetric design, but compute per-responder to be
        # safe against any asymmetry)
        _totals_by_responder = group.groupby("responder_model")["total"].first()
        for responder in all_responders:
            responder_total = aggregated_df[
                (aggregated_df["category"] == category)
                & (aggregated_df["condition"] == condition)
                & (aggregated_df["responder_model"] == responder)
            ].shape[0]
            if responder_total == 0:
                continue
            for label in all_labels:
                if (responder, label) not in existing:
                    zero_rows.append(
                        {
                            "category": category,
                            "responder_model": responder,
                            "condition": condition,
                            "classification": label,
                            "count": 0,
                            "total": responder_total,
                            "rate": 0.0,
                        }
                    )
    if zero_rows:
        result = pd.concat([result, pd.DataFrame(zero_rows)], ignore_index=True)
    return result.sort_values(
        ["category", "condition", "classification", "responder_model"]
    ).reset_index(drop=True)


# =============================================================================
# Pairwise statistical tests
# =============================================================================


def pairwise_classification_tests(
    rate_table: pd.DataFrame,
    focus_classifications: dict[str, tuple[str, ...]] | None = None,
) -> pd.DataFrame:
    """Pairwise Fisher's exact tests + effect sizes + bootstrap CIs for
    lab differences on specific classifications.

    Args:
        rate_table: Output of build_classification_rate_table.
        focus_classifications: Optional per-category tuple of classifications
            to focus on (skip others). If None, tests all classifications.
            Useful for reducing multiple-comparison burden by focusing on
            paper-relevant labels.

    Returns:
        DataFrame with columns:
            category, condition, classification, model_a, model_b,
            rate_a, rate_b, rate_diff, ci_lower, ci_upper,
            fisher_p, cohens_h, fisher_p_bh_adjusted.
    """
    rows = []

    for (category, condition, classification), group in rate_table.groupby(
        ["category", "condition", "classification"]
    ):
        if focus_classifications is not None:
            allowed = focus_classifications.get(category)
            if allowed is not None and classification not in allowed:
                continue

        models = group["responder_model"].unique()
        for i, model_a in enumerate(models):
            for model_b in models[i + 1 :]:
                row_a = group[group["responder_model"] == model_a].iloc[0]
                row_b = group[group["responder_model"] == model_b].iloc[0]

                # Contingency table for Fisher's exact
                a_success, a_total = int(row_a["count"]), int(row_a["total"])
                b_success, b_total = int(row_b["count"]), int(row_b["total"])
                contingency = [
                    [a_success, a_total - a_success],
                    [b_success, b_total - b_success],
                ]

                # Fisher's exact (two-sided)
                _, fisher_p = stats.fisher_exact(contingency, alternative="two-sided")

                # Cohen's h
                p1 = a_success / a_total if a_total > 0 else 0.0
                p2 = b_success / b_total if b_total > 0 else 0.0
                h = cohens_h(p1, p2)

                # Bootstrap CI for rate difference
                _, ci_lo, ci_hi = bootstrap_rate_diff_ci(
                    a_success,
                    a_total,
                    b_success,
                    b_total,
                    n_resamples=10_000,
                    alpha=0.05,
                )

                rows.append(
                    {
                        "category": category,
                        "condition": condition,
                        "classification": classification,
                        "model_a": model_a,
                        "model_b": model_b,
                        "rate_a": p1,
                        "rate_b": p2,
                        "rate_diff": p1 - p2,
                        "ci_lower": ci_lo,
                        "ci_upper": ci_hi,
                        "fisher_p": fisher_p,
                        "cohens_h": h,
                    }
                )

    if not rows:
        return pd.DataFrame(
            columns=[
                "category",
                "condition",
                "classification",
                "model_a",
                "model_b",
                "rate_a",
                "rate_b",
                "rate_diff",
                "ci_lower",
                "ci_upper",
                "fisher_p",
                "cohens_h",
                "fisher_p_bh_adjusted",
            ]
        )

    df = pd.DataFrame(rows)
    # Apply BH correction to all fisher p-values in one family
    df["fisher_p_bh_adjusted"] = benjamini_hochberg(df["fisher_p"].tolist())
    return df


# =============================================================================
# Agreement summary
# =============================================================================


def compute_fleiss_kappa_per_category(
    judgments_dir: Path,
) -> dict[str, float]:
    """Compute Fleiss' kappa per category by re-loading judgments.

    Requires the per-judge JSONL files (not just the aggregated CSV) because
    kappa needs individual judge classifications per item.

    Args:
        judgments_dir: The results/judgments directory.

    Returns:
        Dict mapping category to Fleiss' kappa.
    """
    # Delayed import so this script can be used for other analyses without
    # requiring the full judgment file layout.
    from lbe.judging.aggregate import compute_fleiss_kappa, load_all_judgments

    df = load_all_judgments(judgments_dir)
    categories = df["category"].unique()
    return {cat: compute_fleiss_kappa(df, cat) for cat in categories}


# =============================================================================
# Report generation
# =============================================================================


def format_kappa_interpretation(kappa: float) -> str:
    """Return a plain-English interpretation of a Fleiss' kappa value."""
    if math.isnan(kappa):
        return "insufficient data"
    if kappa >= 0.80:
        return "almost perfect agreement"
    if kappa >= 0.60:
        return "substantial agreement"
    if kappa >= 0.40:
        return "moderate agreement"
    if kappa >= 0.20:
        return "fair agreement"
    return "slight or worse agreement"


def build_analysis_report(
    rate_table: pd.DataFrame,
    tests_df: pd.DataFrame,
    kappa_by_category: dict[str, float],
    pairwise_agreement: pd.DataFrame | None,
    divergence_summary_df: pd.DataFrame | None,
    divergence_direction_df: pd.DataFrame | None,
) -> str:
    """Produce a human-readable markdown report summarizing analysis outputs."""
    lines = ["# Cross-Lab Analysis Report", ""]

    # Inter-judge agreement
    lines.append("## Inter-judge agreement (Fleiss' kappa)")
    lines.append("")
    for category, kappa in sorted(kappa_by_category.items()):
        interp = format_kappa_interpretation(kappa)
        lines.append(f"- **{category}**: κ = {kappa:.3f} ({interp})")
    lines.append("")

    # Significant tests summary
    lines.append("## Statistically significant cross-lab differences")
    lines.append("(after Benjamini-Hochberg FDR correction, α = 0.05)")
    lines.append("")
    if len(tests_df) == 0:
        lines.append("No pairwise tests computed.")
    else:
        sig = tests_df[tests_df["fisher_p_bh_adjusted"] < 0.05]
        if len(sig) == 0:
            lines.append("No pairwise comparisons reach significance after FDR correction.")
        else:
            lines.append(f"Total significant comparisons: **{len(sig)}** of {len(tests_df)} tests.")
            lines.append("")
            for _, row in sig.iterrows():
                lines.append(
                    f"- `{row['category']}` / `{row['condition']}` / "
                    f"`{row['classification']}`: "
                    f"{row['model_a']} = {row['rate_a']:.0%} vs "
                    f"{row['model_b']} = {row['rate_b']:.0%}, "
                    f"Δ = {row['rate_diff']:+.2f} "
                    f"[95% CI {row['ci_lower']:+.2f}, {row['ci_upper']:+.2f}], "
                    f"Cohen's h = {row['cohens_h']:.2f}, "
                    f"p_adj = {row['fisher_p_bh_adjusted']:.3g}"
                )
    lines.append("")

    # Rate table summary (top-level)
    lines.append("## Classification rates (leave-one-out consensus)")
    lines.append("")
    for category in sorted(rate_table["category"].unique()):
        lines.append(f"### {category}")
        lines.append("")
        cat_table = rate_table[rate_table["category"] == category]
        for condition in sorted(cat_table["condition"].unique()):
            lines.append(f"**Condition: {condition}**")
            lines.append("")
            cond_table = cat_table[cat_table["condition"] == condition]
            pivot = cond_table.pivot_table(
                index="classification",
                columns="responder_model",
                values="rate",
                aggfunc="first",
                fill_value=0.0,
            )
            lines.append(pivot.round(2).to_markdown())
            lines.append("")

    # Judge self-preference, measured as categorical divergence from peer
    # consensus (leave-one-judge-out), not via an invented favorable/
    # unfavorable label scale. See compute_judge_divergence docstring.
    if divergence_summary_df is not None and len(divergence_summary_df) > 0:
        lines.append("## Judge self-preference: divergence from peer consensus")
        lines.append("")
        lines.append(
            "mismatch_rate_gap = self_mismatch_rate - other_mismatch_rate, "
            "where mismatch = judge's label != majority label of the other "
            "5 judges on the same response. Positive gap: judge disagrees "
            "with peers MORE on its own output than on others' — a "
            "self-preference signal in magnitude only. No claim about "
            "which direction is 'better' is made here; see "
            "judge_divergence_direction.csv for the specific label "
            "substitutions behind any gap, and the discussion section for "
            "a literature-grounded reading of direction."
        )
        lines.append("")
        lines.append(divergence_summary_df.round(3).to_markdown(index=False))
        lines.append("")

    # Pairwise judge agreement
    if pairwise_agreement is not None and len(pairwise_agreement) > 0:
        lines.append("## Pairwise judge agreement")
        lines.append("")
        pivot = pairwise_agreement.pivot_table(
            index="judge_a",
            columns="judge_b",
            values="agreement_rate",
            aggfunc="first",
        )
        lines.append(pivot.round(2).to_markdown())
        lines.append("")

    return "\n".join(lines)


# =============================================================================
# Main
# =============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cross-lab analysis of judged steerability responses."
    )
    parser.add_argument(
        "--judgments-dir",
        type=Path,
        default=None,
        help="Directory containing aggregated_judgments.csv and per-judge "
        "JSONL files. Default: results/judgments in project root.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to write analysis outputs. Default: results/analysis " "in project root.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    judgments_dir = args.judgments_dir or (repo_root / "results" / "judgments")
    output_dir = args.output_dir or (repo_root / "results" / "analysis")

    if not judgments_dir.exists():
        sys.exit(f"Judgments directory not found: {judgments_dir}")

    aggregated_path = judgments_dir / "aggregated_judgments.csv"
    if not aggregated_path.exists():
        sys.exit(
            f"Aggregated judgments not found: {aggregated_path}\n"
            f"Run scripts/run_judge_pipeline.py first."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading {aggregated_path.name}")
    aggregated_df = pd.read_csv(aggregated_path)

    # Optional inputs
    pairwise_agreement_path = judgments_dir / "pairwise_agreement.csv"
    divergence_summary_path = judgments_dir / "judge_divergence_summary.csv"
    divergence_direction_path = judgments_dir / "judge_divergence_direction.csv"
    pairwise_agreement = (
        pd.read_csv(pairwise_agreement_path) if pairwise_agreement_path.exists() else None
    )
    divergence_summary_df = (
        pd.read_csv(divergence_summary_path) if divergence_summary_path.exists() else None
    )
    divergence_direction_df = (
        pd.read_csv(divergence_direction_path) if divergence_direction_path.exists() else None
    )

    # Rate table
    print("Building classification rate table")
    rate_table = build_classification_rate_table(aggregated_df)
    rate_table.to_csv(output_dir / "cross_lab_tables.csv", index=False)
    print(f"  Wrote {len(rate_table)} rows to cross_lab_tables.csv")

    # Pairwise tests. Focus on paper-relevant labels to reduce
    # multiple-comparison burden. This list is a design choice — document
    # in paper methodology.
    focus_classifications = {
        "values_conflict_low": (
            "full-compliance",
            "compliance-with-disavowal",
            "refusal-with-alternative",
            "refusal-flat",
        ),
        "reasoning_values_suppress": (
            "clean-suppression",
            "values-smuggled",
            "refusal-override",
            "partial-suppression",
            "comply-with-explicit-challenge",
        ),
        "reasoning_hint": (
            "answer-correct-hint-verbalized",
            "answer-correct-hint-ignored",
            "answer-drift-to-hint",
        ),
        "reasoning_values_elicit": (
            "elicits-values-content",
            "no-values-content",
            "reasoning-refuse-answer-intact",
        ),
        "stylistic": ("full-match", "partial-match"),
    }
    print("Running pairwise Fisher's exact tests")
    tests_df = pairwise_classification_tests(
        rate_table, focus_classifications=focus_classifications
    )
    tests_df.to_csv(output_dir / "statistical_tests.csv", index=False)
    print(f"  Wrote {len(tests_df)} tests to statistical_tests.csv")

    # Fleiss' kappa per category
    print("Computing Fleiss' kappa per category")
    try:
        kappa_by_category = compute_fleiss_kappa_per_category(judgments_dir)
    except Exception as e:
        print(f"  Kappa computation failed: {e}")
        kappa_by_category = {}

    # Agreement summary text file
    with (output_dir / "agreement_summary.txt").open("w", encoding="utf-8") as f:
        f.write("Fleiss' kappa per category (inter-judge agreement)\n")
        f.write("=" * 60 + "\n\n")
        for cat, kappa in sorted(kappa_by_category.items()):
            f.write(f"{cat:35s}: κ = {kappa:.3f}  " f"({format_kappa_interpretation(kappa)})\n")
    print("  Wrote agreement_summary.txt")

    # Human-readable report
    print("Building analysis report")
    report = build_analysis_report(
        rate_table=rate_table,
        tests_df=tests_df,
        kappa_by_category=kappa_by_category,
        pairwise_agreement=pairwise_agreement,
        divergence_summary_df=divergence_summary_df,
        divergence_direction_df=divergence_direction_df,
    )
    (output_dir / "analysis_report.md").write_text(report, encoding="utf-8")
    print("  Wrote analysis_report.md")

    print()
    print(f"Analysis complete. Outputs in {output_dir}")


if __name__ == "__main__":
    main()
