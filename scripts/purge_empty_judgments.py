"""purge_empty_judgments.py -- find and remove empty-classification rows
that were written into the MAIN judgment files (not the errors files) when
a judge call failed. The pipeline's resume logic treats these as "already
judged" and refuses to re-attempt them, so they must be purged before a
re-run will fill the real gaps.

Default is a DRY RUN (audit only, nothing changed). Pass --purge to actually
remove the empty rows; each modified file is backed up to .prepurge.bak first.

Usage:
    python purge_empty_judgments.py            # audit all files
    python purge_empty_judgments.py --purge    # actually remove empty rows
"""

import json
import shutil
import sys
from pathlib import Path

JUDGMENTS_DIR = Path("results/judgments")


def main() -> None:
    do_purge = "--purge" in sys.argv

    main_files = sorted(JUDGMENTS_DIR.glob("judge_*.jsonl"))
    main_files = [f for f in main_files if not f.name.endswith(".errors.jsonl")]

    print(f"{'File':<70} {'Real':>6} {'Empty':>6}")
    print("-" * 84)

    total_empty = 0
    files_with_empties = []
    for path in main_files:
        real_rows = []
        empty_count = 0
        with path.open() as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec.get("classification", "").strip():
                    real_rows.append(line)
                else:
                    empty_count += 1

        if empty_count:
            files_with_empties.append((path, real_rows, empty_count))
            total_empty += empty_count
            marker = "  <-- has empties"
        else:
            marker = ""
        print(f"{path.name:<70} {len(real_rows):>6} {empty_count:>6}{marker}")

        if do_purge and empty_count:
            backup = path.with_name(path.name + ".prepurge.bak")
            shutil.copy2(path, backup)
            with path.open("w") as f:
                f.writelines(real_rows)

    print("-" * 84)
    print(f"Files with empty rows: {len(files_with_empties)}")
    print(f"Total empty rows across all files: {total_empty}")

    if not do_purge:
        if total_empty:
            print(
                f"\nDRY RUN — nothing changed. {total_empty} empty rows would be "
                f"removed across {len(files_with_empties)} file(s).\n"
                f"Re-run with --purge to remove them (backups written as "
                f".prepurge.bak), then re-run the judge pipeline for the affected "
                f"responders to fill the now-genuinely-missing judgments."
            )
        else:
            print("\nNo empty rows found. Main files are clean.")
    else:
        print(
            f"\nPurged {total_empty} empty rows. Backups saved as *.prepurge.bak\n"
            f"Now re-run the judge pipeline for the affected responders so the "
            f"missing judgments get filled:\n"
            f"  python scripts/run_judge_pipeline.py --responders <model> "
            f"--items-file steerability_items_v3.jsonl"
        )


if __name__ == "__main__":
    main()
