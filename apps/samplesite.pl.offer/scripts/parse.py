"""Parsing layer: the fragile, site-specific part. Keep it isolated here.

Builder note: this is where ~90% of per-target work lives. Three jobs:
  find_records(html)   -> list of raw record chunks on a page
  parse_record(raw)    -> one flat dict (matches CSV columns)
  next_page_url(...)   -> URL of the next page, or None when done

The template below targets a fictional structure and returns nothing real."""
from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup  # parse backend: lxml (fast, forgiving). CSS via soupsieve.

PARSER = "lxml"

# CSV columns are derived from one real record during the MODEL phase.
COLUMNS = ["id", "title", "price", "location", "url"]


def find_records(html: str) -> list:
    """Return the repeating record elements on a listing page. TEMPLATE selector."""
    soup = BeautifulSoup(html, PARSER)
    # TODO(builder): real selector, e.g. soup.select("div.offer-card")
    return soup.select("div.offer-card")


def parse_record(raw) -> dict:
    """Map one record element to a flat dict keyed by COLUMNS. TEMPLATE values."""
    def text(sel: str) -> str:
        node = raw.select_one(sel)
        return node.get_text(strip=True) if node else ""

    return {
        "id": raw.get("data-id", ""),
        "title": text("h2.title"),
        "price": text("span.price"),
        "location": text("span.location"),
        "url": text("a.detail-link"),
    }


def next_page_url(html: str, current_url: str) -> str | None:
    """Find the next-page link, or None to end the crawl. TEMPLATE: single page."""
    soup = BeautifulSoup(html, PARSER)
    node = soup.select_one("a.pagination-next")
    if node and node.get("href"):
        return urljoin(current_url, node["href"])
    return None
