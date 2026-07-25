"""Shared error classification for API failures.

Distinguishes fatal, section-wide conditions (quota exhaustion, billing
failure, invalid credentials, model access restrictions) from transient,
per-item failures, and produces a clean, human-readable summary rather than
the raw provider exception text, which is long, inconsistently formatted
JSON that isn't useful to read at a glance mid-run.

Where the provider tells us how long to wait (Gemini's `retryDelay` field,
or a "retry in Xh Ym Zs" phrase in the message body), that duration is
extracted and reported alongside the current time, so a report reads as
"quota exceeded, retry after ~8h (available at 2026-07-19 22:14:03)" rather
than requiring you to do that math from a raw error dump yourself.

Used by both retry_errors.py and rerun_items.py so the two scripts can't
silently disagree about what counts as fatal or how a report is formatted.
run_judges.py's FatalJudgeError wraps the original provider error's repr()
as its message, so classify_error() works uniformly whether it's given a
raw provider exception (the rerun_items.py / generation case) or a caught
FatalJudgeError (the retry_errors.py / judging case).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

# (substring to match in lowercased error text, category). Order matters:
# first match wins, so more specific markers should precede general ones.
_FATAL_PATTERNS: tuple[tuple[str, str], ...] = (
    ("insufficient_quota", "QUOTA_EXCEEDED"),
    ("exceeded your current quota", "QUOTA_EXCEEDED"),
    ("resource_exhausted", "QUOTA_EXCEEDED"),
    ("no longer available to new users", "MODEL_ACCESS"),
    ("invalid_api_key", "AUTH_ERROR"),
    ("invalid x-api-key", "AUTH_ERROR"),
    ("authentication", "AUTH_ERROR"),
    ("permission_denied", "AUTH_ERROR"),
    ("billing", "BILLING_ERROR"),
)

_CATEGORY_SUMMARIES: dict[str, str] = {
    "QUOTA_EXCEEDED": "API quota exceeded for this account/project.",
    "MODEL_ACCESS": "This model is not accessible with the current API key/project.",
    "AUTH_ERROR": "Authentication failed -- check the API key.",
    "BILLING_ERROR": "Billing issue on this account.",
    "OTHER": "Unclassified error (treated as non-fatal; not retried automatically).",
}

# Gemini-style machine-readable field: 'retryDelay': '12345s'
_RETRY_DELAY_PATTERN = re.compile(r"retryDelay['\"]?\s*:\s*['\"](\d+(?:\.\d+)?)s['\"]")
# Human-phrased fallback: "retry in 20h39m51.28s" / "retry in 45s" / etc.
# Every group is optional so partial phrasings (just minutes, just seconds)
# still parse; a match requires at least one group to be present.
_RETRY_IN_PATTERN = re.compile(
    r"retry in\s*(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*(?:(\d+(?:\.\d+)?)\s*s)?",
    re.IGNORECASE,
)


@dataclass
class ClassifiedError:
    """Result of classifying an exception.

    Attributes:
        category: One of QUOTA_EXCEEDED, MODEL_ACCESS, AUTH_ERROR,
            BILLING_ERROR, or OTHER.
        summary: Short, human-readable description of the category.
        is_fatal: True if this category should abort the current
            combo/model run rather than being retried per-item.
        retry_after_seconds: Provider-supplied wait duration, if present
            in the error text. None if not found or not applicable.
    """

    category: str
    summary: str
    is_fatal: bool
    retry_after_seconds: float | None = None


def _extract_retry_seconds(text: str) -> float | None:
    """Pull a retry-after duration out of provider error text, if present."""
    match = _RETRY_DELAY_PATTERN.search(text)
    if match:
        return float(match.group(1))

    match = _RETRY_IN_PATTERN.search(text)
    if match and any(match.groups()):
        hours = float(match.group(1) or 0)
        minutes = float(match.group(2) or 0)
        seconds = float(match.group(3) or 0)
        total = hours * 3600 + minutes * 60 + seconds
        return total if total > 0 else None
    return None


def classify_error(exc: BaseException) -> ClassifiedError:
    """Classify an exception into a category with a clean summary.

    Args:
        exc: The raised exception. Works on a raw provider exception or on
            a wrapper (e.g. FatalJudgeError) whose string form contains the
            original provider error text.

    Returns:
        A ClassifiedError describing the failure.
    """
    text = str(exc)
    lower = text.lower()

    category = "OTHER"
    for marker, cat in _FATAL_PATTERNS:
        if marker in lower:
            category = cat
            break

    is_fatal = category != "OTHER"
    retry_after = _extract_retry_seconds(text) if is_fatal else None

    return ClassifiedError(
        category=category,
        summary=_CATEGORY_SUMMARIES[category],
        is_fatal=is_fatal,
        retry_after_seconds=retry_after,
    )


def format_error_report(exc: BaseException, *, context: str = "") -> str:
    """Render a classified error as a clean, human-readable report.

    Includes the current timestamp and, if the provider supplied a retry
    duration, the estimated time the quota/limit becomes available again.
    Deliberately omits the raw provider exception text -- that's available
    via classify_error() plus str(exc) if ever needed for deeper debugging,
    but isn't printed by default since it's long, inconsistently formatted
    JSON that adds noise rather than clarity mid-run.

    Args:
        exc: The exception to report on.
        context: Optional short prefix describing what was being attempted
            (e.g. "judge=google:gemini-2.5-pro responder=openai:gpt-5"),
            prepended to the report.

    Returns:
        A multi-line report string, ready to print.
    """
    classified = classify_error(exc)
    now = datetime.now()
    header = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}]"
    if context:
        header += f" {context}"

    lines = [f"{header} -- {classified.category}: {classified.summary}"]

    if classified.retry_after_seconds is not None:
        reset_time = now + timedelta(seconds=classified.retry_after_seconds)
        hrs = int(classified.retry_after_seconds // 3600)
        mins = int((classified.retry_after_seconds % 3600) // 60)
        lines.append(
            f"  Provider says retry after ~{hrs}h {mins}m "
            f"(estimated available at {reset_time.strftime('%Y-%m-%d %H:%M:%S')})"
        )
    elif classified.is_fatal:
        lines.append("  No retry duration was provided by the API for this error.")

    return "\n".join(lines)
