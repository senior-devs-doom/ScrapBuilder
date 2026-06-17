"""
Builder-side SCOUT artifact grabber — saves raw HTML snapshots to disk for study.

Why raw (not document.body.innerHTML): old PHP/WordPress sites send the COMPLETE data
in the raw HTTP response, including <head> (ld+json, generator, encoding hints) that
innerHTML throws away — at zero browser cost. We only need a rendered DOM dump when the
raw HTML is a JS shell, and this tool detects that case and tells you.

Usage:
    python utils/snapshot.py <url> <out.html>
    python utils/snapshot.py https://books.toscrape.com apps/books.toscrape.com/_scout/mainsite.html

It writes the HTML file and prints a compact report: size, encoding, title, and a
JS-shell verdict (whether you must escalate to Tier 4 / Playwright).
"""
from __future__ import annotations

import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

UA = "ScrapBuilder-Scout/0.1 (+https://github.com/scrapbuilder)"
SHELL_MARKERS = ("__NEXT_DATA__", "window.__INITIAL_STATE__", "id=\"root\"", "id=\"app\"", "ng-app")


def js_shell_verdict(html: str) -> tuple[bool, str]:
    """Heuristic: is the data missing from raw HTML (i.e. JS must render it)?"""
    soup = BeautifulSoup(html, "lxml")
    body = soup.body
    visible = len(body.get_text(strip=True)) if body else 0
    scripts = len(soup.find_all("script"))
    ratio = visible / max(len(html), 1)
    has_marker = any(m in html for m in SHELL_MARKERS)
    # Lots of markup, almost no visible text, framework root markers => likely a shell.
    if visible < 500 and ratio < 0.05 and (has_marker or scripts > 3):
        return True, f"LIKELY JS SHELL (visible_text={visible}, ratio={ratio:.3f}, scripts={scripts}) -> consider Tier 4 render"
    return False, f"server-rendered OK (visible_text={visible}, ratio={ratio:.3f}, scripts={scripts}) -> Tier 1-3 viable"


def snapshot(url: str, out_path: str) -> None:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    s = requests.Session()
    s.headers["User-Agent"] = UA
    r = s.get(url, timeout=25)
    r.encoding = r.apparent_encoding or r.encoding
    html = r.text
    out.write_text(html, encoding="utf-8")

    soup = BeautifulSoup(html, "lxml")
    title = (soup.title.get_text(strip=True) if soup.title else "")[:80]
    is_shell, verdict = js_shell_verdict(html)

    print(f"== SNAPSHOT {url}")
    print(f"   status={r.status_code} final={r.url}")
    print(f"   content-type={r.headers.get('content-type')}  encoding={r.encoding}")
    print(f"   saved {len(html):,} bytes -> {out}")
    print(f"   title: {title!r}")
    print(f"   verdict: {verdict}")
    if is_shell:
        print("   NOTE: raw HTML looks empty of data. The browser dump (innerHTML) would")
        print("         differ — escalate to Playwright only after confirming no hidden JSON.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python utils/snapshot.py <url> <out.html>")
        raise SystemExit(2)
    snapshot(sys.argv[1], sys.argv[2])
