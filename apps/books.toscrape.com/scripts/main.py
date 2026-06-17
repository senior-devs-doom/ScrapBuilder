"""
books.toscrape.com crawler — dumps the full catalogue to books.csv + books.xlsx.

A sandbox site built for scraping practice (no robots restrictions). Archetype B+C:
server-rendered listing with page-N pagination + a detail page per book. Tier 2.

Run via run.bat, or from the app folder:
    python scripts/main.py                 # full crawl: 50 listing pages, ~1000 books + details
    python scripts/main.py --max-pages 2   # quick slice (verification)
    python scripts/main.py --no-detail     # listing fields only; skip per-book detail fetch
"""
from __future__ import annotations

import sys
from pathlib import Path

# Put the app root on sys.path so `from scripts.xxx import yyy` resolves correctly
# regardless of how this file is invoked (via run.bat or directly).
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    sys.stdout.reconfigure(encoding="utf-8")  # cp1250 console safety (£ etc.)
except Exception:
    pass

from scripts.fetch import Fetcher
from scripts.parse import find_cards, parse_card, parse_detail, next_page_url
from scripts.export import write_csv, write_xlsx

APP_DIR = Path(__file__).parent.parent
START_URL = "https://books.toscrape.com/catalogue/page-1.html"
OUTPUT_CSV = APP_DIR / "books.csv"
OUTPUT_XLSX = APP_DIR / "books.xlsx"
MAX_PAGES = 50
RATE_LIMIT_SECONDS = 0.5
USER_AGENT = "ScrapBuilder/0.1 (books.toscrape.com sandbox; see README.txt)"


def crawl(max_pages: int, fetch_detail: bool) -> list[dict]:
    fetcher = Fetcher(user_agent=USER_AGENT, rate_limit=RATE_LIMIT_SECONDS)
    rows: list[dict] = []
    url = START_URL
    pages = 0
    while url and pages < max_pages:
        pages += 1
        html = fetcher.get(url)
        cards = find_cards(html)
        if not cards:
            print("  no books on page — stopping.")
            break
        print(f"[page {pages}] {len(cards)} books — {url}")
        for card in cards:
            rec = parse_card(card, url)
            if fetch_detail and rec.get("product_url"):
                try:
                    rec.update(parse_detail(fetcher.get(rec["product_url"])))
                except Exception as e:  # skip a bad detail, keep the listing row
                    print(f"  WARN detail failed for {rec.get('title','?')}: {e}")
            rows.append(rec)
        url = next_page_url(html, url)
    return rows


def main() -> int:
    args = sys.argv[1:]
    max_pages = MAX_PAGES
    if "--max-pages" in args:
        max_pages = int(args[args.index("--max-pages") + 1])
    fetch_detail = "--no-detail" not in args

    print(f"Crawling books.toscrape.com (max_pages={max_pages}, detail={fetch_detail})")
    rows = crawl(max_pages, fetch_detail)
    if not rows:
        print("No rows collected.")
        return 1
    write_csv(rows, OUTPUT_CSV)
    write_xlsx(rows, OUTPUT_XLSX)
    print(f"Done. Wrote {len(rows)} books -> {OUTPUT_CSV.name} + {OUTPUT_XLSX.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
