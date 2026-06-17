"""Export layer: list[dict] -> CSV + XLSX. Stable column order, utf-8-sig for Excel."""
from __future__ import annotations

import csv
from pathlib import Path

from scripts.parse import COLUMNS


def write_csv(rows: list[dict], path: Path, columns: list[str] | None = None) -> None:
    cols = columns or COLUMNS
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in cols})


def write_xlsx(rows: list[dict], path: Path, columns: list[str] | None = None) -> None:
    import openpyxl
    cols = columns or COLUMNS
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(cols)
    for row in rows:
        ws.append([row.get(c, "") for c in cols])
    wb.save(path)
