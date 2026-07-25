"""judging_status.py -- rigorous picture of judging progress.

Unlike a raw line count, this checks:
  1. How many UNIQUE (item_id, condition) judgments exist per pair
     (duplicates would inflate a raw count without representing real progress)
  2. Whether any duplicates exist at all -- a sign a retry appended without
     properly clearing the old entry
  3. Outstanding errors per pair
  4. Whether every item ID that SHOULD be judged actually appears somewhere
     (either successful or in the error file) -- catches items that vanished
     from both during an interrupted retry

Usage:
    python judging_status.py data/steerability_items_v3.jsonl
"""

import json
import sys
from collections import Counter
from pathlib import Path

JUDGMENTS_DIR = Path("results/judgments")
CORE_CATEGORIES = {
    "values_conflict_low",
    "reasoning_values_elicit",
    "reasoning_values_suppress",
}
# Sanity-check categories from v2 are still valid/unchanged and should still
# count toward "complete" for pairs judged before the v3 expansion.
SANITY_CATEGORIES = {"stylistic", "reasoning_hint"}


def load_expected_keys(items_path: Path) -> set[tuple[str, str]]:
    """Every (item_id, condition) that should eventually have a judgment."""
    keys = set()
    with items_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            keys.add((item["id"], "base"))
            keys.add((item["id"], "steered"))
    return keys


def load_v2_sanity_keys(v2_path: Path) -> set[tuple[str, str]]:
    """Sanity-category (item_id, condition) keys, which persist from v2
    and were never part of the v3 core-category expansion."""
    keys = set()
    if not v2_path.exists():
        return keys
    with v2_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            if item.get("category") in SANITY_CATEGORIES:
                keys.add((item["id"], "base"))
                keys.add((item["id"], "steered"))
    return keys


def read_keys_and_check_dupes(path: Path) -> tuple[set, list]:
    """Returns (unique keys present, list of duplicate keys found)."""
    if not path.exists():
        return set(), []
    counter: Counter = Counter()
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            key = (rec["item_id"], rec["condition"])
            counter[key] += 1
    dupes = [k for k, c in counter.items() if c > 1]
    return set(counter.keys()), dupes


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage: python judging_status.py <v3_items_path> [v2_items_path]")

    v3_path = Path(sys.argv[1])
    v2_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/steerability_items_v2.jsonl")

    v3_keys = load_expected_keys(v3_path)
    sanity_keys = load_v2_sanity_keys(v2_path)
    expected_keys = v3_keys | sanity_keys
    expected_total = len(expected_keys)

    print(f"Expected unique (item_id, condition) judgments per pair: {expected_total}")
    print(
        f"  ({len(v3_keys)} from v3 core categories + {len(sanity_keys)} from v2 sanity categories)\n"  # noqa: E501
    )

    main_files = sorted(JUDGMENTS_DIR.glob("judge_*.jsonl"))
    main_files = [f for f in main_files if not f.name.endswith(".errors.jsonl")]

    rows = []
    any_dupes = False
    for path in main_files:
        stem = path.stem.removeprefix("judge_")
        if "_on_" not in stem:
            continue
        judge, responder = stem.split("_on_", 1)

        success_keys, dupes = read_keys_and_check_dupes(path)
        # NOTE: do not use path.with_suffix() here -- pathlib decides
        # "suffix" by the LAST dot in the filename, and model names like
        # gemini-2.5-pro and Qwen3.7-Max contain a literal dot in the
        # version number, which silently mangles the constructed path.
        # Exact string-suffix replacement avoids that entirely.
        error_path = path.with_name(path.name[: -len(".jsonl")] + ".errors.jsonl")
        error_keys, error_dupes = read_keys_and_check_dupes(error_path)

        missing = expected_keys - success_keys - error_keys
        pct = 100 * len(success_keys) / expected_total if expected_total else 0

        rows.append(
            (judge, responder, len(success_keys), len(error_keys), len(missing), len(dupes), pct)
        )
        if dupes:
            any_dupes = True
    # noqa: E501
    rows.sort(key=lambda r: r[6])

    print(
        f"{'Judge':<38} {'Responder':<38} {'OK':>6} {'Err':>6} {'Missing':>8} {'Dupes':>6} {'%':>6}"
    )
    print("-" * 112)
    total_ok = total_err = total_missing = total_dupes = 0
    for judge, responder, ok, err, missing, dupes, pct in rows:
        flag = ""  # noqa: E501
        if dupes:
            flag += "  <-- DUPLICATES, INVESTIGATE"
        if missing:
            flag += f"  <-- {missing} MISSING (neither success nor error)"
        print(
            f"{judge:<38} {responder:<38} {ok:>6} {err:>6} {missing:>8} {dupes:>6} {pct:>5.1f}%{flag}"  # noqa: E501
        )
        total_ok += ok
        total_err += err
        total_missing += missing
        total_dupes += dupes

    print("-" * 112)
    print(f"TOTAL unique successful judgments: {total_ok}")
    print(f"TOTAL error records outstanding: {total_err}")
    print(f"TOTAL missing (in neither file): {total_missing}")
    print(f"TOTAL duplicate keys found: {total_dupes}")

    if any_dupes:
        print(
            "\nWARNING: duplicates found. These likely represent a retry that "
            "appended a new judgment without removing an old one for the same "
            "item+condition. Aggregation may pick the wrong one arbitrarily. "
            "Investigate before running aggregate.py."
        )
    if total_missing:
        print(
            "\nWARNING: some (item_id, condition) pairs appear in NEITHER the "
            "main file nor the errors file for at least one judge/responder "
            "pair -- likely lost during an interrupted retry. These need to "
            "be re-judged from scratch; they won't be picked up automatically."
        )


if __name__ == "__main__":
    main()
