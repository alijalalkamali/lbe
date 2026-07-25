#!/usr/bin/env python3
"""validate_v3_items.py

Sanity-checks steerability_items_v3.jsonl before any API calls are made
against it. Catching a malformed item here costs nothing; catching it after
generating and judging costs real money.

Checks:
  1. Exactly 300 items, 100 per category, only the 3 core categories
     (values_conflict_low, reasoning_values_elicit, reasoning_values_suppress)
  2. No duplicate item IDs
  3. Every item has all required non-empty fields
  4. The first 20 items per category are byte-identical to v2 (same IDs,
     same base_prompt/steering_instruction/expected_behavior_change) --
     confirms the "first 20 unchanged" claim rather than assuming it
  5. No sanity-check categories (stylistic, reasoning_hint) leaked in

Usage:
    python validate_v3_items.py data/steerability_items_v2.jsonl data/steerability_items_v3.jsonl
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict

REQUIRED_FIELDS = (
    "id",
    "category",
    "item_type",
    "base_prompt",
    "steering_instruction",
    "expected_behavior_change",
)
CORE_CATEGORIES = {
    "values_conflict_low",
    "reasoning_values_elicit",
    "reasoning_values_suppress",
}
BANNED_CATEGORIES = {"stylistic", "reasoning_hint"}
EXPECTED_PER_CATEGORY = 100
EXPECTED_TOTAL = 300


def load_jsonl(path: str) -> list[dict]:
    items = []
    with open(path) as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"FAIL  {path}:{i} is not valid JSON: {e}")
                sys.exit(1)
    return items


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("Usage: python validate_v3_items.py <v2_path> <v3_path>")

    v2_path, v3_path = sys.argv[1], sys.argv[2]
    v2_items = load_jsonl(v2_path)
    v3_items = load_jsonl(v3_path)

    fail = False

    def check(desc: str, ok: bool) -> None:
        nonlocal fail
        print(f"{'PASS' if ok else 'FAIL'}  {desc}")
        if not ok:
            fail = True

    # 1. Total count and per-category counts
    check(f"v3 has exactly {EXPECTED_TOTAL} items", len(v3_items) == EXPECTED_TOTAL)

    by_category: dict[str, list[dict]] = defaultdict(list)
    for item in v3_items:
        by_category[item.get("category", "MISSING")].append(item)

    check(
        "only the 3 core categories present, no sanity categories",
        set(by_category.keys()) == CORE_CATEGORIES
        and not (set(by_category.keys()) & BANNED_CATEGORIES),
    )
    if set(by_category.keys()) & BANNED_CATEGORIES:
        print(f"      found banned categories: {set(by_category.keys()) & BANNED_CATEGORIES}")  # noqa: E501

    for cat in CORE_CATEGORIES:
        n = len(by_category.get(cat, []))
        check(
            f"category '{cat}' has exactly {EXPECTED_PER_CATEGORY} items",
            n == EXPECTED_PER_CATEGORY,
        )

    # 2. No duplicate IDs
    all_ids = [item.get("id", "MISSING") for item in v3_items]
    dupes = {i for i in all_ids if all_ids.count(i) > 1}
    check("no duplicate item IDs", len(dupes) == 0)
    if dupes:
        print(f"      duplicates: {sorted(dupes)}")

    # 3. Required fields non-empty
    bad_items = []
    for item in v3_items:
        for field in REQUIRED_FIELDS:
            val = item.get(field)
            if val is None or (isinstance(val, str) and not val.strip()):
                bad_items.append((item.get("id", "UNKNOWN"), field))
    check("all items have non-empty required fields", len(bad_items) == 0)
    for item_id, field in bad_items[:20]:
        print(f"      {item_id}: missing/empty '{field}'")
    if len(bad_items) > 20:
        print(f"      ... and {len(bad_items) - 20} more")

    # 4. First 20 per category match v2 exactly
    v2_by_id = {item["id"]: item for item in v2_items}
    v3_by_id = {item["id"]: item for item in v3_items}

    v2_ids_by_category: dict[str, list[str]] = defaultdict(list)
    for item in v2_items:
        if item.get("category") in CORE_CATEGORIES:
            v2_ids_by_category[item["category"]].append(item["id"])

    mismatches = []
    missing_from_v3 = []
    fields_to_compare = ("base_prompt", "steering_instruction", "expected_behavior_change")
    for _cat, ids in v2_ids_by_category.items():
        for item_id in ids:
            if item_id not in v3_by_id:
                missing_from_v3.append(item_id)
                continue
            v2_item, v3_item = v2_by_id[item_id], v3_by_id[item_id]
            for field in fields_to_compare:
                if v2_item.get(field) != v3_item.get(field):
                    mismatches.append((item_id, field))

    check(
        "all v2 core-category items present in v3 with identical content",
        len(mismatches) == 0 and len(missing_from_v3) == 0,
    )
    for item_id in missing_from_v3:
        print(f"      MISSING from v3: {item_id}")
    for item_id, field in mismatches:
        print(f"      CONTENT MISMATCH: {item_id}.{field} differs between v2 and v3")

    # 5. Report the new item IDs (useful for Step 2 -- targeted generation)
    v2_ids_all = set(v2_by_id.keys())
    new_ids = sorted(set(v3_by_id.keys()) - v2_ids_all)
    print(f"\nNew item IDs in v3 (not in v2): {len(new_ids)}")
    if len(new_ids) == 240:
        print("      count matches expected (240 new items)")
    else:
        print(f"      WARNING: expected 240 new items, found {len(new_ids)}")
        fail = True

    with open("new_item_ids.txt", "w") as f:
        f.write("\n".join(new_ids) + "\n")
    print("      written to new_item_ids.txt for use in Step 2")

    print()
    if fail:
        print("SOME CHECKS FAILED -- do not generate/judge against this file yet.")
        sys.exit(1)
    else:
        print("ALL CHECKS PASSED -- safe to proceed to generation.")


if __name__ == "__main__":
    main()
