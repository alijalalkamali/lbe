"""Shared utilities for API model backends.

Retry logic and common constants used by all provider-specific backends.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

DEFAULT_TIMEOUT = 120.0  # seconds
DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0  # seconds


def retry_with_backoff(
    fn: Callable[[], T],
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
) -> T:
    """Call fn, retrying with exponential backoff on any exception.

    Total attempts: max_retries + 1 (initial + retries).
    Delays between retries: base_delay * 2^attempt seconds.
    Defaults produce delays of 1s, 2s, 4s (3 retries).

    Raises the final exception if all attempts fail.

    Args:
        fn: Zero-argument callable returning the API response.
        max_retries: Number of retries after the initial call.
        base_delay: Base delay in seconds; doubled at each retry.

    Returns:
        Whatever fn returns on success.

    Raises:
        The final exception if all attempts fail.
    """
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception:
            if attempt == max_retries:
                raise
            time.sleep(base_delay * (2**attempt))
    # Unreachable; satisfies type checker
    raise RuntimeError("retry_with_backoff exited loop unexpectedly")
