"""Shared utilities for API model backends.

Retry logic and common constants used by all provider-specific backends.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

from lbe.models.error_utils import classify_error

T = TypeVar("T")

DEFAULT_TIMEOUT = 120.0  # seconds
DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0  # seconds


def retry_with_backoff(
    fn: Callable[[], T],
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
) -> T:
    """Call fn, retrying with exponential backoff on transient exceptions.

    A FATAL exception (quota exhaustion, billing failure, invalid
    credentials, or a model access restriction -- see
    lbe.models.error_utils.classify_error) is raised immediately on the
    first attempt, with NO retry and NO delay. These conditions fail
    identically on every attempt, so retrying wastes time (the backoff
    delays) and money (each retry is itself a real, doomed API call) without
    any chance of succeeding. Only genuinely transient errors (a brief
    network blip, a momentary timeout) get the backoff retries this
    function was built for.

    Total attempts for a transient error: max_retries + 1 (initial + retries).
    Delays between retries: base_delay * 2^attempt seconds.
    Defaults produce delays of 1s, 2s, 4s (3 retries).

    Raises the final exception if all attempts fail.

    Args:
        fn: Zero-argument callable returning the API response.
        max_retries: Number of retries after the initial call. Ignored for
            fatal errors, which always raise on the first attempt.
        base_delay: Base delay in seconds; doubled at each retry.

    Returns:
        Whatever fn returns on success.

    Raises:
        The triggering exception. Immediately, with no retry, if it was
        classified as fatal. After exhausting max_retries otherwise.
    """
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as e:
            if classify_error(e).is_fatal:
                # Quota/billing/auth/access conditions fail identically on
                # every attempt -- don't waste retries or delay on them.
                raise
            if attempt == max_retries:
                raise
            time.sleep(base_delay * (2**attempt))
    # Unreachable; satisfies type checker
    raise RuntimeError("retry_with_backoff exited loop unexpectedly")
