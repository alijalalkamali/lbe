"""Exact power analysis for the pairwise Fisher testing regime.

Computes the exact power of Fisher's exact test to detect a 30%-vs-0%
classification-rate difference between two models, at a stringent alpha
(0.001) representative of the effective threshold the Benjamini-Hochberg
correction imposes across the full pairwise sweep.

This reproduces, exactly, the design-phase Monte Carlo estimates that
motivated the N=20 -> N=100 item expansion (simulated values at the time:
0.05 / 0.40 / 0.69 / 0.92 / 0.98 for N = 20/30/40/50/60). Because the
null-side rate is exactly zero, no simulation is required: the second
group's count is 0 with probability 1, so power is the binomial-weighted
sum over the first group's possible counts of an indicator that the
resulting 2x2 table clears the threshold.

Usage:
    python scripts/power_analysis.py

Output: one line per sample size with exact power, matching the values
reported in the paper's Statistical Analysis section.
"""

from __future__ import annotations

from scipy import stats

# Effect size and threshold match the design-phase analysis: a 30-point
# rate difference against a zero rate, tested at alpha=0.001 as a
# stand-in for a typical BH-corrected significance threshold at the
# scale of this study's pairwise sweep.
EFFECT_RATE: float = 0.30
NULL_RATE: float = 0.0
ALPHA: float = 0.001
SAMPLE_SIZES: tuple[int, ...] = (20, 30, 40, 50, 60, 80, 100)


def exact_power(n_per_group: int, effect_rate: float, alpha: float) -> float:
    """Exact power of Fisher's exact test for effect_rate vs. a true zero rate.

    With a true rate of exactly 0 in the second group, its observed count
    is always 0, so the only randomness is the first group's binomial
    count. Power is the probability mass of counts whose resulting table
    yields a Fisher p-value below alpha.

    Args:
        n_per_group: Number of items per model (equal group sizes).
        effect_rate: True classification rate in the first group.
        alpha: Significance threshold.

    Returns:
        Exact power in [0, 1].
    """
    power = 0.0
    for count in range(n_per_group + 1):
        table = [[count, n_per_group - count], [0, n_per_group]]
        _, p_value = stats.fisher_exact(table)
        if p_value < alpha:
            power += stats.binom.pmf(count, n_per_group, effect_rate)
    return power


def main() -> None:
    print(f"Exact power: {EFFECT_RATE:.0%} vs {NULL_RATE:.0%}, Fisher's exact test, alpha={ALPHA}")
    for n in SAMPLE_SIZES:
        print(f"  N={n:3d} per model: power = {exact_power(n, EFFECT_RATE, ALPHA):.4f}")


if __name__ == "__main__":
    main()
