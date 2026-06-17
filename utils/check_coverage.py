"""
Builder-side coverage checker.

Usage:
    python utils/check_coverage.py <path/to/file.csv>
    python utils/check_coverage.py <path/to/file.csv> --sparse-threshold 30

Reads a scraped CSV and reports per-column fill rates. Run after a sample crawl
(--max-pages 3+) to catch broken selectors before committing to a full pull.

Three outcomes per column:
  ✓  OK     -- >=50% of records have a value (healthy or legitimately dense)
  ~  SPARSE -- >0% but <50% fill -- might be genuinely optional, might be broken;
               investigate: does the field appear later in the dataset?
  ✗  BROKEN -- 0% fill -- selector returned nothing for any record; fix before full run.

Exit 0 = no BROKEN columns.  Exit 1 = at least one BROKEN column.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DEFAULT_SPARSE_THRESHOLD = 50


def check(csv_path: Path, sparse_threshold: int = DEFAULT_SPARSE_THRESHOLD) -> int:
    try:
        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            columns = list(reader.fieldnames or [])
    except FileNotFoundError:
        print(f"ERROR: file not found — {csv_path}")
        return 1

    if not rows:
        print(f"ERROR: {csv_path.name} has no rows.")
        return 1

    n = len(rows)
    print(f"\nCoverage: {csv_path}  ({n} rows, {len(columns)} columns)")
    print("-" * 72)

    broken: list[str] = []
    sparse: list[str] = []

    for col in columns:
        non_empty = [r.get(col, "").strip() for r in rows if r.get(col, "").strip()]
        filled = len(non_empty)
        pct = filled / n * 100
        sample = non_empty[0][:55] if non_empty else ""

        if filled == 0:
            tag = "✗ BROKEN"
            broken.append(col)
        elif pct < sparse_threshold:
            tag = "~ SPARSE"
            sparse.append(col)
        else:
            tag = "✓"

        bar = f"{filled:>4}/{n} ({pct:5.1f}%)"
        note = f'  e.g. "{sample}"' if sample else "  ← no value in any record"
        print(f"  {tag:<10}  {col:<22}  {bar}{note}")

    print()
    if broken:
        print(f"BROKEN — {len(broken)} column(s) with 0% fill (selector is wrong or field")
        print(f"         doesn't exist in the source). Fix before running the full crawl:")
        for c in broken:
            print(f"  • {c}")
    if sparse:
        print(f"SPARSE — {len(sparse)} column(s) with <{sparse_threshold}% fill:")
        print(f"  {', '.join(sparse)}")
        print( "  → Is the field genuinely optional in the source?")
        print( "    If yes: expected. If no: pull more pages or inspect mid-dataset records.")
    if not broken and not sparse:
        print("All columns OK. ✓")

    return 1 if broken else 0


if __name__ == "__main__":
    argv = sys.argv[1:]
    if not argv:
        print(f"Usage: python {sys.argv[0]} <path/to/file.csv> [--sparse-threshold N]")
        sys.exit(1)

    path = Path(argv[0])
    threshold = DEFAULT_SPARSE_THRESHOLD
    if "--sparse-threshold" in argv:
        threshold = int(argv[argv.index("--sparse-threshold") + 1])

    sys.exit(check(path, threshold))
