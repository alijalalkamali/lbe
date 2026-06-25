"""Rule-based scorers for steerability eval items.

Each scoring function takes a response string and returns a numerical metric
appropriate to the category. The metric is then compared between base and
steered responses to determine whether steering changed behavior as expected.

Not all categories have a rule-based scorer. Categories without one return
None from `measure()`, signaling that LLM-judge scoring is needed (added later).
"""

import re
from collections.abc import Callable

# A scorer takes a response text and returns a numerical metric, or None if
# the category cannot be scored by rules.
Scorer = Callable[[str], float | None]


def _count_sentences(text: str) -> int:
    """Approximate sentence count by counting terminators (. ! ?)."""
    # Filter out empty splits from trailing punctuation.
    parts = re.split(r"[.!?]+", text.strip())
    return len([p for p in parts if p.strip()])


def _count_words(text: str) -> int:
    """Whitespace-delimited word count."""
    return len(text.split())


def score_length_control(response: str) -> float:
    """Sentence count as the relevant metric for length_control items."""
    return float(_count_sentences(response))


def score_format(response: str) -> float | None:
    """Detect structural format. Returns a categorical-as-numeric label.

    0.0 = prose, 1.0 = numbered list, 2.0 = bulleted list, 3.0 = table.

    Numeric output is for storage compatibility with EvalResult.score; the
    interpretation is categorical and handled at the analysis layer.
    """
    text = response.strip()
    if not text:
        return 0.0
    # Table heuristic: pipes on multiple lines suggest markdown table.
    pipe_lines = sum(1 for line in text.split("\n") if line.count("|") >= 2)
    if pipe_lines >= 2:
        return 3.0
    # Numbered list: lines starting with "1.", "2.", "1)", etc.
    if re.search(r"(?m)^\s*\d+[.)]\s+", text):
        return 1.0
    # Bulleted list: lines starting with "-", "*", "•".
    if re.search(r"(?m)^\s*[-*•]\s+", text):
        return 2.0
    return 0.0


# Categories without a rule-based scorer — explicitly return None.
def score_unsupported(response: str) -> None:
    return None


# Registry mapping category name → scorer function.
SCORERS: dict[str, Scorer] = {
    "length_control": score_length_control,
    "format": score_format,
    "tone": score_unsupported,
    "balance": score_unsupported,
    "persona": score_unsupported,
    "reasoning_style": score_unsupported,
    "audience_adaptation": score_unsupported,
}


def measure(category: str, response: str) -> float | None:
    """Compute the rule-based metric for a response in the given category.

    Returns None if the category has no rule-based scorer (LLM-judge needed).
    Raises ValueError on unknown categories so missing entries fail loudly.
    """
    if category not in SCORERS:
        raise ValueError(
            f"Unknown category: {category!r}. " f"Known categories: {sorted(SCORERS.keys())}"
        )
    return SCORERS[category](response)
