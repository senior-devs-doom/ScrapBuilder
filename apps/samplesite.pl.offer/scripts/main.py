"""
samplesite.pl.offer — TEMPLATE crawler app (non-functional).

This is the canonical shape every ScrapBuilder app follows. The builder agent copies
this folder and specializes fetch/parse for a real target. Run via run.bat, or from
the app folder:

    python scripts/main.py

It pulls the whole dataset from the target and writes <site>.csv + <site>.xlsx next
to the scripts/ folder (in the app root). Depends only on the shared venv — no agent,
no API keys.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Put the app root on sys.path so `from scripts.xxx import yyy` resolves correctly
# regardless of how this file is invoked (via run.bat or directly).
sys.path.insert(0, str(Path(__file__).parent.parent))

# Windows consoles default to cp1250 (PL) and crash when printing £/€/non-ASCII data.
# Force utf-8 so progress prints never kill an otherwise-fine run. (CSV is utf-8-sig.)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from scripts.fetch import Fetcher
from scripts.parse import parse_record, find_records, next_page_url
from scripts.export import write_csv, write_xlsx


def _load_contact() -> str:
    """Read contact email from project-root creds.txt (gitignored). Silent if missing."""
    creds = Path(__file__).parent.parent.parent / "creds.txt"
    if creds.exists():
        for line in creds.read_text().splitlines():
            if line.startswith("contact="):
                return line.split("=", 1)[1].strip()
    return ""


# --- Config (the builder fills these in per target) ----------------------------
APP_DIR = Path(__file__).parent.parent
START_URL = "https://samplesite.pl/offer"          # TODO: real entry point
OUTPUT_CSV = APP_DIR / f"{APP_DIR.name}.csv"
OUTPUT_XLSX = APP_DIR / f"{APP_DIR.name}.xlsx"
MAX_PAGES = 1000                                    # safety cap against runaway loops
RATE_LIMIT_SECONDS = 1.0
_contact = _load_contact()
USER_AGENT = f"ScrapBuilder/0.1 (samplesite.pl.offer{'; ' + _contact if _contact else ''})"
# -------------------------------------------------------------------------------


def crawl() -> list[dict]:
    """Scraper cycle: pull -> locate -> traverse all -> collect rows."""
    fetcher = Fetcher(user_agent=USER_AGENT, rate_limit=RATE_LIMIT_SECONDS)
    rows: list[dict] = []
    url = START_URL
    pages = 0

    while url and pages < MAX_PAGES:
        pages += 1
        print(f"[{pages}] fetching {url}")
        html = fetcher.get(url)
        records = find_records(html)
        if not records:
            print("  no records on page — stopping.")
            break
        for raw in records:
            try:
                rows.append(parse_record(raw))
            except Exception as e:  # skip a bad record, don't crash the run
                print(f"  WARN skipped a record: {e}")
        url = next_page_url(html, url)

    return rows


def main() -> int:
    print("This is a TEMPLATE app and does not target a real site yet.")
    print("The ScrapBuilder agent specializes scripts/fetch.py and scripts/parse.py.")
    rows = crawl()
    if not rows:
        print("No rows collected (expected for the template).")
        return 0
    write_csv(rows, OUTPUT_CSV)
    write_xlsx(rows, OUTPUT_XLSX)
    print(f"Done. Wrote {len(rows)} rows -> {OUTPUT_CSV.name} + {OUTPUT_XLSX.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
