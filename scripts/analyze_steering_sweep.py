"""
Analyze the judged steering sweep: derail rate as a function of alpha.

Consensus rule mirrors the main pipeline's spirit at pseudo-model scale:
majority label across judges per (item, alpha). One self-judgment concern
carries over: Llama-3.3 judging generations produced by (steered) Llama-3.3
weights. The main pipeline handles self-preference by leave-one-out; here
the responder name ("steered:L40:alpha+3") never string-matches the judge,
so LOO-by-name is inert. We therefore report BOTH consensus over all six
judges and consensus excluding the Llama judge; if the two disagree
materially, the Llama-excluded version is the honest headline.

For each alpha, the derail rate on the 50 held-out items is compared to the
alpha=0 control arm by Fisher's exact test (matching the main paper's
test choice for small-cell proportions).

Usage:
    python scripts/analyze_steering_sweep.py \
        --judgments-dir results/interp/judgments \
        --output-csv results/interp/steering_rates.csv
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

from scipy.stats import fisher_exact

from lbe.io.jsonl import read_jsonl
from lbe.judging.run_judges import JudgmentRecord

LLAMA_JUDGE = "together:meta-llama/Llama-3.3-70B-Instruct-Turbo"


def _majority(labels: list[str]) -> str | None:
    """Strict plurality winner; None on a tie for first place."""
    if not labels:
        return None
    counts = Counter(labels).most_common()
    if len(counts) > 1 and counts[0][1] == counts[1][1]:
        return None
    return counts[0][0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--judgments-dir", type=Path, default=Path("results/interp/judgments"))
    parser.add_argument(
        "--output-csv", type=Path, default=Path("results/interp/steering_rates.csv")
    )
    parser.add_argument("--positive-label", default="derail")
    args = parser.parse_args()

    files = sorted(args.judgments_dir.glob("judge_*_on_steered*.jsonl"))
    files = [f for f in files if not f.name.endswith(".errors.jsonl")]
    if not files:
        raise SystemExit(f"No judgment files under {args.judgments_dir}.")

    # (alpha, item_id) -> {judge: label}
    by_key: dict[tuple[float, str], dict[str, str]] = defaultdict(dict)
    for path in files:
        for rec in read_jsonl(path, JudgmentRecord):
            if not rec.classification.strip() or rec.error:
                continue
            m = re.search(r"alpha([+-][\d.]+)", rec.responder_model)
            if not m:
                raise SystemExit(f"Cannot parse alpha from {rec.responder_model!r}")
            alpha = float(m.group(1))
            by_key[(alpha, rec.item_id)][rec.judge_model] = rec.classification

    rows = []
    per_alpha: dict[float, dict[str, int]] = defaultdict(
        lambda: {
            "derail_all": 0,
            "n_all": 0,
            "derail_noL": 0,
            "n_noL": 0,
            "ties_all": 0,
            "incomplete": 0,
        }
    )
    for (alpha, item_id), judge_labels in sorted(by_key.items()):
        s = per_alpha[alpha]
        if len(judge_labels) < 4:
            s["incomplete"] += 1
            continue
        all_labels = list(judge_labels.values())
        no_llama = [lab for j, lab in judge_labels.items() if j != LLAMA_JUDGE]

        maj_all = _majority(all_labels)
        maj_no_llama = _majority(no_llama)
        if maj_all is None:
            s["ties_all"] += 1
        else:
            s["n_all"] += 1
            s["derail_all"] += int(maj_all == args.positive_label)
        if maj_no_llama is not None:
            s["n_noL"] += 1
            s["derail_noL"] += int(maj_no_llama == args.positive_label)
        rows.append(
            {
                "alpha": alpha,
                "item_id": item_id,
                "consensus_all": maj_all or "TIE",
                "consensus_no_llama": maj_no_llama or "TIE",
                "n_judges": len(judge_labels),
            }
        )

    if 0.0 not in per_alpha:
        raise SystemExit("No alpha=0 control arm found -- cannot compute contrasts.")
    ctrl = per_alpha[0.0]

    print(
        f"{'alpha':>7} {'derail(all6)':>14} {'derail(noLlama)':>16} "
        f"{'p vs a=0':>10} {'ties':>5} {'incompl':>8}"
    )
    summary_rows = []
    for alpha in sorted(per_alpha):
        s = per_alpha[alpha]
        rate_all = s["derail_all"] / s["n_all"] if s["n_all"] else float("nan")
        rate_no_llama = s["derail_noL"] / s["n_noL"] if s["n_noL"] else float("nan")
        if alpha == 0.0 or not s["n_all"] or not ctrl["n_all"]:
            p = float("nan")
        else:
            table = [
                [s["derail_all"], s["n_all"] - s["derail_all"]],
                [ctrl["derail_all"], ctrl["n_all"] - ctrl["derail_all"]],
            ]
            p = fisher_exact(table)[1]
        print(
            f"{alpha:>7.1f} {s['derail_all']:>3}/{s['n_all']:<3} ({rate_all:.2f}) "
            f"{s['derail_noL']:>3}/{s['n_noL']:<3} ({rate_no_llama:.2f}) "
            f"{p:>10.4g} {s['ties_all']:>5} {s['incomplete']:>8}"
        )
        summary_rows.append(
            {
                "alpha": alpha,
                "derail_all6": s["derail_all"],
                "n_all6": s["n_all"],
                "rate_all6": round(rate_all, 4),
                "derail_no_llama": s["derail_noL"],
                "n_no_llama": s["n_noL"],
                "rate_no_llama": round(rate_no_llama, 4),
                "fisher_p_vs_control_all6": p,
                "ties_all6": s["ties_all"],
                "incomplete_lt4_judges": s["incomplete"],
            }
        )

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        w.writeheader()
        w.writerows(summary_rows)
    per_item_csv = args.output_csv.with_name(args.output_csv.stem + "_per_item.csv")
    with per_item_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {args.output_csv} and {per_item_csv}")


if __name__ == "__main__":
    main()
