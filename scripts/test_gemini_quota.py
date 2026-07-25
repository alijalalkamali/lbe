"""test_gemini_quota.py -- fires N small sequential calls to check whether
the Gemini daily quota is fully reset, partially available, or still
exhausted. Standalone, bypasses the pipeline entirely so a bug elsewhere
can't muddy this specific diagnostic.

Usage:
    python test_gemini_quota.py [n_calls]
"""

import sys
import time

from lbe.models.google_backend import GoogleBackend

n = int(sys.argv[1]) if len(sys.argv) > 1 else 8

model = GoogleBackend("gemini-2.5-pro")

successes = 0
failures = 0
for i in range(1, n + 1):
    try:
        result = model.generate(f"Say the number {i}.", max_new_tokens=10)
        print(f"[{i}/{n}] SUCCESS  finish_reason={result.finish_reason!r}  text={result.text!r}")
        successes += 1
    except Exception as e:
        print(f"[{i}/{n}] FAILED   {type(e).__name__}: {str(e)[:150]}")
        failures += 1
    time.sleep(1)  # small gap to avoid tripping a separate per-second rate limit

print()
print(f"Total: {successes} succeeded, {failures} failed out of {n}")
if successes == n:
    print("Quota looks fully reset -- safe to run the real retry.")
elif successes == 0:
    print("Still fully exhausted -- wait longer before retrying.")
else:
    print(f"Partial availability ({successes} slots) -- quota reset is likely still rolling in.")
