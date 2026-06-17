"""
probe_detail.py — SCOUT helper: find and snapshot detail/sub-page links from a listing.

Given a saved listing snapshot HTML, extracts candidate per-item or sub-section links,
prints them ranked by likelihood, and optionally fetches + snapshots the top candidate
for comparison with the listing.

Usage:
    python utils/probe_detail.py <listing_html> <base_url> [--out-dir <dir>] [--no-fetch]

Example:
    python utils/probe_detail.py apps/mysite/_scout/listing.html https://mysite.com \
        --out-dir apps/mysite/_scout/

Output:
    - Ranked list of candidate detail links
    - Saves <out-dir>/detail_sample.html (first candidate) and runs validate_scout on it
    - Reports text-length delta (detail vs listing) as a signal that more data is present
"""
import argparse
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

UA = "ScrapBuilder-Scout/0.1 (+https://github.com/scrapbuilder)"
MAX_CANDIDATES = 10


def score_link(href: str, base_netloc: str) -> int:
    """Higher = more likely a detail/subpage link. Returns -1 to exclude."""
    parsed = urlparse(href)
    # Must be same domain or relative
    if parsed.netloc and parsed.netloc != base_netloc:
        return -1
    path = parsed.path.rstrip("/")
    if not path or path in ("/", "#"):
        return -1
    # Prefer paths with multiple segments (depth > 1) = detail page
    depth = len([p for p in path.split("/") if p])
    # Prefer paths with ID-like segments (digits, slugs with dashes)
    segments = path.split("/")
    last = segments[-1] if segments else ""
    has_id = any(c.isdigit() for c in last)
    has_slug = "-" in last and len(last) > 5
    score = depth * 10
    if has_id:
        score += 15
    if has_slug:
        score += 10
    # Penalise pagination, anchors, common non-data paths
    for skip in ("/page/", "/tag/", "/category/", "/feed", ".css", ".js", ".xml",
                 "/login", "/cart", "/checkout", "/search", "#"):
        if skip in href:
            return -1
    return score


def extract_candidates(html: str, base_url: str) -> list[str]:
    base_netloc = urlparse(base_url).netloc
    soup = BeautifulSoup(html, "lxml")
    seen: dict[str, int] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href:
            continue
        full = urljoin(base_url, href)
        s = score_link(full, base_netloc)
        if s >= 0:
            seen[full] = max(seen.get(full, 0), s)
    ranked = sorted(seen.items(), key=lambda x: -x[1])
    return [url for url, _ in ranked[:MAX_CANDIDATES]]


def fetch_and_save(url: str, out_path: Path) -> str:
    s = requests.Session()
    s.headers["User-Agent"] = UA
    r = s.get(url, timeout=25)
    r.encoding = r.apparent_encoding or r.encoding
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(r.text, encoding="utf-8")
    return r.text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("listing_html")
    ap.add_argument("base_url")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--no-fetch", action="store_true")
    args = ap.parse_args()

    listing_path = Path(args.listing_html)
    if not listing_path.exists():
        print(f"ERROR: {listing_path} not found", file=sys.stderr)
        sys.exit(2)

    html = listing_path.read_text(encoding="utf-8", errors="replace")
    listing_text_len = len(BeautifulSoup(html, "lxml").get_text(strip=True))

    candidates = extract_candidates(html, args.base_url)
    if not candidates:
        print("[probe_detail] No candidate detail/sub-page links found in listing.")
        sys.exit(0)

    print(f"[probe_detail] {len(candidates)} candidate link(s) from {listing_path.name}:")
    for i, url in enumerate(candidates, 1):
        print(f"  {i:2}. {url}")

    if args.no_fetch:
        sys.exit(0)

    # Snapshot the top candidate
    top = candidates[0]
    out_dir = Path(args.out_dir) if args.out_dir else listing_path.parent
    out_file = out_dir / "detail_sample.html"
    print(f"\n[probe_detail] Fetching top candidate: {top}")
    detail_html = fetch_and_save(top, out_file)
    detail_text_len = len(BeautifulSoup(detail_html, "lxml").get_text(strip=True))
    print(f"[probe_detail] Saved -> {out_file}")
    print(f"[probe_detail] Text size: listing={listing_text_len:,} vs detail={detail_text_len:,}", end="")
    delta = detail_text_len - listing_text_len
    if delta > 200:
        print(f"  (+{delta:,}) -> detail has more content, likely richer data")
    elif delta < -200:
        print(f"  ({delta:,}) -> detail has LESS content than listing (unexpected, check manually)")
    else:
        print("  (similar size, check manually)")

    print(f"\n[probe_detail] Next: python utils/validate_scout.py {out_file}")


if __name__ == "__main__":
    main()
