"""
Builder-side discovery probes — run by the AGENT during SCOUT, NOT shipped in apps.

Cheap reconnaissance to characterize a target before committing to a cost tier.
Usage:
    python utils/discovery.py https://samplesite.pl/offer
"""
from __future__ import annotations

import sys
from urllib.parse import urljoin, urlparse

import requests

UA = "ScrapBuilder-Scout/0.1 (+https://github.com/ scrapbuilder)"
HIDDEN_JSON_GUESSES = [
    "/wp-json/", "/wp-json/wp/v2/posts?per_page=1",
    "/sitemap.xml", "/sitemap_index.xml", "/robots.txt",
    "/api/", "/wp-admin/admin-ajax.php",
]
JSON_MARKERS = ("application/ld+json", "__NEXT_DATA__", "window.__INITIAL_STATE__")


def probe(url: str) -> None:
    parts = urlparse(url)
    root = f"{parts.scheme}://{parts.netloc}"
    s = requests.Session()
    s.headers["User-Agent"] = UA

    # 1. Entry point character
    r = s.get(url, timeout=20)
    print(f"\n== ENTRY {url}")
    print(f"   status={r.status_code} final={r.url} type={r.headers.get('content-type')}")
    for h in ("server", "x-powered-by", "x-wp-totalpages", "set-cookie"):
        if h in r.headers:
            print(f"   {h}: {r.headers[h][:120]}")
    body = r.text
    print(f"   html_len={len(body)}")
    for m in JSON_MARKERS:
        if m in body:
            print(f"   embedded-json marker found: {m}")

    # 2. Hidden endpoint guesses (cheap HEAD-ish GETs)
    print("\n== HIDDEN-DATA PROBES")
    for path in HIDDEN_JSON_GUESSES:
        target = urljoin(root, path)
        try:
            pr = s.get(target, timeout=15)
            ct = pr.headers.get("content-type", "")
            hot = "json" in ct or "xml" in ct
            flag = "  <-- candidate" if hot and pr.status_code < 400 else ""
            print(f"   {pr.status_code} {ct[:30]:30} {target}{flag}")
        except Exception as e:  # noqa: BLE001
            print(f"   ERR {target}: {e}")

    print("\nNext: pick a cost tier + archetype (see docs/TOOLS.md, docs/CASES.md).")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python utils/discovery.py <url>")
        raise SystemExit(2)
    probe(sys.argv[1])
