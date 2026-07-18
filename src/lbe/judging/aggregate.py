"""Aggregation of multi-judge classifications.

Reads per-judge JSONL files and computes:
    - Majority-vote consensus per (item, responder, condition)
    - Leave-one-out consensus (excluding self-judgment for peer-review-among-
      models analysis)
    - Inter-judge agreement (Fleiss' kappa across all judges per category)
    - Self-preference bias per judge (rate at which judge selects favorable
      classifications for own outputs vs others)
    - Pairwise judge agreement matrix

Output is a single CSV (aggregated_judgments.csv) with one row per
(item, responder, condition) containing the consensus classifications
and per-judge classifications for downstream analysis.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pandas as pd

from lbe.io.jsonl import read_jsonl
from lbe.judging.run_judges import JudgmentRecord


def load_all_judgments(judgments_dir: Path) -> pd.DataFrame:
    """Load all per-judge JSONL files in a directory into one DataFrame.

    Args:
        judgments_dir: Directory containing judge_<judge>_on_<responder>.jsonl
            files.

    Returns:
        DataFrame with all judgments, one row per judgment.
        Columns include: item_id, category, responder_model, condition,
        judge_model, classification, justification, cited_text, confidence,
        error.
    """
    all_records: list[dict] = []
    for jsonl_path in sorted(judgments_dir.glob("judge_*.jsonl")):
        # Skip error-log files: they duplicate a subset of records already
        # present in the main judge output file (every errored record is
        # written to both), and their filenames also end in ".jsonl" so
        # they match this glob pattern too. Not excluding them double-counts
        # every errored judgment in downstream record counts.
        if jsonl_path.name.endswith(".errors.jsonl"):
            continue
        for record in read_jsonl(jsonl_path, JudgmentRecord):
            all_records.append(record.model_dump())

    if not all_records:
        raise FileNotFoundError(f"No judge_*.jsonl files found in {judgments_dir}")
    return pd.DataFrame(all_records)


def _majority_vote(labels: list[str]) -> tuple[str, int]:
    """Return the majority-vote label and its count.

    Ties broken by lexicographic order (deterministic).

    Args:
        labels: List of classification labels from multiple judges.

    Returns:
        Tuple of (majority_label, count).
    """
    if not labels:
        return "", 0
    counter = Counter(labels)
    max_count = max(counter.values())
    # Break ties deterministically
    tied = sorted(label for label, c in counter.items() if c == max_count)
    return tied[0], max_count


def compute_consensus(df: pd.DataFrame) -> pd.DataFrame:
    """Compute majority-vote consensus and leave-one-out consensus per
    (item_id, responder_model, condition).

    Leave-one-out consensus excludes the judgment where judge_model ==
    responder_model. This is the peer-review-among-models analog: each
    response is judged by all its peers, not by itself.

    Args:
        df: Long-format DataFrame from load_all_judgments.

    Returns:
        Wide-format DataFrame with one row per (item_id, responder_model,
        condition), columns for each judge's classification, plus consensus
        and leave-one-out consensus.
    """
    # Filter out error rows for consensus computation
    good = df[df["error"] == ""].copy()

    # Pivot to wide: one row per (item, responder, condition), columns per judge
    wide = good.pivot_table(
        index=["item_id", "category", "responder_model", "condition"],
        columns="judge_model",
        values="classification",
        aggfunc="first",
    ).reset_index()

    def _row_consensus(row: pd.Series) -> pd.Series:
        judges = [
            c
            for c in wide.columns
            if c not in {"item_id", "category", "responder_model", "condition"}
        ]
        all_labels = [row[j] for j in judges if pd.notna(row[j])]
        # Leave-one-out: exclude self-judgment
        loo_labels = [row[j] for j in judges if pd.notna(row[j]) and j != row["responder_model"]]
        consensus_label, consensus_count = _majority_vote(all_labels)
        loo_label, loo_count = _majority_vote(loo_labels)
        return pd.Series(
            {
                "consensus": consensus_label,
                "consensus_count": consensus_count,
                "consensus_n_judges": len(all_labels),
                "consensus_loo": loo_label,
                "consensus_loo_count": loo_count,
                "consensus_loo_n_judges": len(loo_labels),
            }
        )

    consensus_cols = wide.apply(_row_consensus, axis=1)
    return pd.concat([wide, consensus_cols], axis=1)


def compute_judge_divergence(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Measure self-preference as categorical divergence from peer consensus,
    with no invented value/favorability scale over rubric labels.

    Method (leave-one-judge-out, distinct from compute_consensus's
    leave-one-*responder*-out): for every (item, responder, condition) row
    and every judge J who classified that row, take the majority-vote label
    among the OTHER 5 judges on that same row (excluding J), then compare
    J's own label against that peer-majority label. This is done once per
    judge per row, so a single row yields 6 comparisons (one where J is the
    responder itself = 'self', five where J is judging another model's
    output = 'other').

    Magnitude of self-preference = the gap between J's mismatch rate with
    peers when judging itself vs. when judging others. A judge with no
    self-preference should disagree with its peers at roughly the same
    rate regardless of who produced the response.

    Direction of self-preference is NOT collapsed into this summary — see
    the second returned DataFrame, which tabulates exactly which labels a
    judge substitutes when it diverges from peers on its own output vs.
    others' output. Any claim about which direction is 'favorable' belongs
    in the paper's discussion section, grounded in cited literature (e.g.
    a resisted/challenged suppression reading as safety-relevant per prior
    work), not in this computation.

    Args:
        df: Long-format DataFrame from load_all_judgments.

    Returns:
        Tuple of (summary_df, direction_df):
            summary_df columns: [judge_model, category, self_mismatch_rate,
                other_mismatch_rate, mismatch_rate_gap, n_self, n_other].
                mismatch_rate_gap = self_mismatch_rate - other_mismatch_rate;
                positive means the judge disagrees with peers MORE on its
                own output than on others' (a self-preference signal in
                either direction — magnitude only, no valence implied).
            direction_df columns: [judge_model, category, is_self,
                own_label, peer_majority_label, count]. Restricted to rows
                where own_label != peer_majority_label. Use this to see
                which specific label substitutions drive the gap above.
    """
    good = df[df["error"] == ""].copy()

    wide = good.pivot_table(
        index=["item_id", "category", "responder_model", "condition"],
        columns="judge_model",
        values="classification",
        aggfunc="first",
    ).reset_index()

    judge_cols = [
        c for c in wide.columns if c not in {"item_id", "category", "responder_model", "condition"}
    ]

    comparison_rows: list[dict] = []
    for _, row in wide.iterrows():
        for judge in judge_cols:
            own_label = row[judge]
            if pd.isna(own_label):
                continue
            peer_labels = [row[j] for j in judge_cols if j != judge and pd.notna(row[j])]
            if not peer_labels:
                continue
            peer_majority_label, _ = _majority_vote(peer_labels)
            comparison_rows.append(
                {
                    "judge_model": judge,
                    "category": row["category"],
                    "responder_model": row["responder_model"],
                    "condition": row["condition"],
                    "is_self": judge == row["responder_model"],
                    "own_label": own_label,
                    "peer_majority_label": peer_majority_label,
                    "match": own_label == peer_majority_label,
                }
            )
    comparisons = pd.DataFrame(comparison_rows)

    # Summary: mismatch rate gap per judge per category
    summary_rows: list[dict] = []
    for judge in comparisons["judge_model"].unique():
        judge_df = comparisons[comparisons["judge_model"] == judge]
        for category in judge_df["category"].unique():
            cat_df = judge_df[judge_df["category"] == category]
            self_df = cat_df[cat_df["is_self"]]
            other_df = cat_df[~cat_df["is_self"]]

            self_mismatch = 1.0 - self_df["match"].mean() if len(self_df) > 0 else float("nan")
            other_mismatch = 1.0 - other_df["match"].mean() if len(other_df) > 0 else float("nan")
            summary_rows.append(
                {
                    "judge_model": judge,
                    "category": category,
                    "self_mismatch_rate": self_mismatch,
                    "other_mismatch_rate": other_mismatch,
                    "mismatch_rate_gap": (
                        self_mismatch - other_mismatch
                        if len(self_df) > 0 and len(other_df) > 0
                        else float("nan")
                    ),
                    "n_self": len(self_df),
                    "n_other": len(other_df),
                }
            )
    summary_df = pd.DataFrame(summary_rows)

    # Direction: label-substitution counts restricted to mismatches
    mismatches = comparisons[~comparisons["match"]]
    direction_df = (
        mismatches.groupby(
            ["judge_model", "category", "is_self", "own_label", "peer_majority_label"]
        )
        .size()
        .reset_index(name="count")
        .sort_values(
            ["judge_model", "category", "is_self", "count"], ascending=[True, True, True, False]
        )
    )

    return summary_df, direction_df


def compute_pairwise_agreement(df: pd.DataFrame) -> pd.DataFrame:
    """Compute pairwise agreement rate between each judge pair.

    For each pair (judge_a, judge_b), computes the rate at which they
    assign the same classification to the same (item, responder,
    condition) tuples.

    Args:
        df: Long-format DataFrame from load_all_judgments.

    Returns:
        Long DataFrame with columns [judge_a, judge_b, agreement_rate, n_shared].
    """
    good = df[df["error"] == ""].copy()
    judges = sorted(good["judge_model"].unique())

    rows: list[dict] = []
    for i, ja in enumerate(judges):
        for jb in judges[i:]:
            a_df = good[good["judge_model"] == ja][
                ["item_id", "responder_model", "condition", "classification"]
            ].rename(columns={"classification": "cls_a"})
            b_df = good[good["judge_model"] == jb][
                ["item_id", "responder_model", "condition", "classification"]
            ].rename(columns={"classification": "cls_b"})
            merged = a_df.merge(
                b_df,
                on=["item_id", "responder_model", "condition"],
                how="inner",
            )
            n_shared = len(merged)
            if n_shared == 0:
                agreement = float("nan")
            else:
                agreement = (merged["cls_a"] == merged["cls_b"]).mean()
            rows.append(
                {
                    "judge_a": ja,
                    "judge_b": jb,
                    "agreement_rate": agreement,
                    "n_shared": n_shared,
                }
            )
    return pd.DataFrame(rows)


def compute_fleiss_kappa(df: pd.DataFrame, category: str) -> float:
    """Compute Fleiss' kappa for inter-judge agreement on one category.

    Fleiss' kappa measures agreement among multiple raters classifying
    items into discrete categories, correcting for chance agreement.
    Range: -1 to 1. Values above 0.8 = 'almost perfect'; 0.6-0.8 =
    'substantial'; below 0.6 = 'moderate or worse'.

    Requires statsmodels. Install with: pip install statsmodels

    Args:
        df: Long-format DataFrame from load_all_judgments.
        category: Category to compute agreement for.

    Returns:
        Fleiss' kappa value, or nan if computation fails.
    """
    try:
        from statsmodels.stats.inter_rater import aggregate_raters, fleiss_kappa
    except ImportError as e:
        raise ImportError(
            "statsmodels is required for Fleiss' kappa. " "Install with: pip install statsmodels"
        ) from e

    good = df[(df["error"] == "") & (df["category"] == category)]

    # Build subject × rating matrix
    # Each row is one (item, responder, condition) tuple; entries are
    # the classifications from each judge.
    wide = good.pivot_table(
        index=["item_id", "responder_model", "condition"],
        columns="judge_model",
        values="classification",
        aggfunc="first",
    ).dropna()

    if len(wide) == 0:
        return float("nan")

    # aggregate_raters expects a matrix where each row is a subject and
    # each column is a rater; entries are category labels.
    ratings_matrix = wide.values
    table, _ = aggregate_raters(ratings_matrix)
    return fleiss_kappa(table)


def save_analysis_ready_csv(
    consensus_df: pd.DataFrame,
    output_path: Path,
) -> None:
    """Save the consensus DataFrame to CSV for downstream analysis.

    Args:
        consensus_df: Output of compute_consensus.
        output_path: Where to write the CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    consensus_df.to_csv(output_path, index=False)
    print(f"Wrote {len(consensus_df)} rows to {output_path}")
