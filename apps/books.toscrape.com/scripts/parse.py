"""Parsing layer for books.toscrape.com (Tier 2, static HTML).

Listing card -> base record; per-book detail page -> enrichment.
Selectors confirmed against _scout/mainsite.html and _scout/subsite.html."""
from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

PARSER = "lxml"

COLUMNS = ["title", "category", "rating", "price_incl", "price_excl", "tax",
           "availability", "stock_qty", "upc", "num_reviews", "description",
           "product_url", "image_url"]

_RATING = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def find_cards(html: str) -> list:
    return BeautifulSoup(html, PARSER).select("article.product_pod")


def parse_card(card, page_url: str) -> dict:
    """One listing card -> base fields (cheap; no extra request)."""
    a = card.select_one("h3 a")
    href = a.get("href", "") if a else ""
    img = card.select_one("img.thumbnail")
    price = card.select_one("p.price_color")
    avail = card.select_one("p.instock.availability")

    rating = ""
    rnode = card.select_one("p.star-rating")
    if rnode:
        for cls in rnode.get("class", []):
            if cls in _RATING:
                rating = _RATING[cls]

    return {
        "title": (a.get("title", "").strip() if a else ""),
        "rating": rating,
        "price_incl": price.get_text(strip=True) if price else "",
        "availability": avail.get_text(strip=True) if avail else "",
        "product_url": urljoin(page_url, href),
        "image_url": urljoin(page_url, img.get("src", "")) if img else "",
    }


def parse_detail(html: str) -> dict:
    """One book detail page -> enrichment fields (UPC, taxes, stock, category, desc)."""
    soup = BeautifulSoup(html, PARSER)

    info: dict[str, str] = {}
    for row in soup.select("table.table-striped tr"):
        th, td = row.select_one("th"), row.select_one("td")
        if th and td:
            info[th.get_text(strip=True)] = td.get_text(strip=True)

    crumbs = soup.select("ul.breadcrumb li a")
    category = crumbs[-1].get_text(strip=True) if crumbs else ""

    desc = soup.select_one("#product_description ~ p")
    description = desc.get_text(strip=True) if desc else ""

    m = re.search(r"(\d+)", info.get("Availability", ""))
    stock_qty = int(m.group(1)) if m else ""

    out = {
        "category": category,
        "price_excl": info.get("Price (excl. tax)", ""),
        "tax": info.get("Tax", ""),
        "stock_qty": stock_qty,
        "upc": info.get("UPC", ""),
        "num_reviews": info.get("Number of reviews", ""),
        "description": description,
    }
    if info.get("Price (incl. tax)"):
        out["price_incl"] = info["Price (incl. tax)"]  # detail is authoritative
    return out


def next_page_url(html: str, page_url: str) -> str | None:
    n = BeautifulSoup(html, PARSER).select_one("li.next a")
    return urljoin(page_url, n["href"]) if n and n.get("href") else None
