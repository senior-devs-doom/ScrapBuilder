"""
probe_detail.py — SCOUT helper: traverse DOWN to the most detailed data entity.

Starting from a listing snapshot, follows links depth-first until reaching the most
granular per-record description available. Target: "the most detailed end description
of a single DB instance" — typically a product detail page, but could be a sub-detail
page, a spec sheet, or a downloadable catalogue document.

Also detects downloadable catalogue documents (PDF/XLSX/CSV) as alternative rich data
sources when no navigable detail pages exist.

Usage:
    python utils/probe_detail.py <listing_html> <base_url> [--out-dir <dir>]
                                 [--no-fetch] [--max-depth N]

Output:
    Depth chain report: listing ->L1 ->L2 (if deeper found)
    Saves each level: detail_depth1.html, detail_depth2.html …
    Flags catalogue documents found at any level
    Warns if no deeper pages found (entry URL may already be the deepest entity)
    Reminds to run validate_scout on each fetched level
"""
import argparse
import subprocess
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

UA = "ScrapBuilder-Scout/0.1"
MAX_CANDIDATES = 10
DOCUMENT_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".csv", ".ods", ".zip"}


def score_link(href: str, base_netloc: str) -> int:
    """Higher = more likely a detail/subpage link. Returns -1 to exclude."""
    parsed = urlparse(href)
    if parsed.netloc and parsed.netloc != base_netloc:
        return -1
    path = parsed.path.rstrip("/")
    if not path or path in ("/", "#"):
        return -1
    depth = len([p for p in path.split("/") if p])
    segments = path.split("/")
    last = segments[-1] if segments else ""
    has_id = any(c.isdigit() for c in last)
    has_slug = "-" in last and len(last) > 5
    score = depth * 10
    if has_id:
        score += 15
    if has_slug:
        score += 10
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


def extract_documents(html: str, base_url: str) -> list[str]:
    """Find downloadable catalogue documents linked from the page."""
    soup = BeautifulSoup(html, "lxml")
    docs = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        ext = Path(urlparse(href).path).suffix.lower()
        if ext in DOCUMENT_EXTENSIONS:
            docs.append(urljoin(base_url, href))
    return list(dict.fromkeys(docs))  # dedupe, preserve order


def fetch_and_save(url: str, out_path: Path) -> str:
    s = requests.Session()
    s.headers["User-Agent"] = UA
    r = s.get(url, timeout=25)
    r.encoding = r.apparent_encoding or r.encoding
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(r.text, encoding="utf-8")
    return r.text


def text_len(html: str) -> int:
    return len(BeautifulSoup(html, "lxml").get_text(strip=True))


def run_validate(path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "validate_scout.py"), str(path)],
        capture_output=True, text=True
    )
    print(result.stdout.strip() or result.stderr.strip())
    if result.returncode == 1:
        print("[probe_detail] !! validate_scout flagged injection — stop and check before reading this page.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("listing_html")
    ap.add_argument("base_url")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--max-depth", type=int, default=2,
                    help="Max levels to traverse below the listing (default 2)")
    args = ap.parse_args()

    listing_path = Path(args.listing_html)
    if not listing_path.exists():
        print(f"ERROR: {listing_path} not found", file=sys.stderr)
        sys.exit(2)

    out_dir = Path(args.out_dir) if args.out_dir else listing_path.parent
    current_html = listing_path.read_text(encoding="utf-8", errors="replace")
    current_url = args.base_url
    current_len = text_len(current_html)

    print(f"[probe_detail] Entry: {listing_path.name}  ({current_len:,} chars)")
    print(f"[probe_detail] Target: deepest data entity (max depth {args.max_depth})\n")

    if args.no_fetch:
        candidates = extract_candidates(current_html, args.base_url)
        docs = extract_documents(current_html, args.base_url)
        print(f"Candidates ({len(candidates)}):")
        for i, u in enumerate(candidates, 1):
            print(f"  {i:2}. {u}")
        if docs:
            print(f"\nCatalogue documents ({len(docs)}):")
            for d in docs:
                print(f"  - {d}")
        sys.exit(0)

    deepest_depth = 0
    deepest_url = current_url

    for depth in range(1, args.max_depth + 1):
        # Check for catalogue documents at this level
        docs = extract_documents(current_html, current_url)
        if docs:
            print(f"[depth {depth}] Catalogue documents found (alternative rich data source):")
            for d in docs:
                print(f"  -> {d}")

        candidates = extract_candidates(current_html, current_url)
        if not candidates:
            if depth == 1:
                print("[probe_detail] No deeper links found in entry page.")
                print("  -> Entry URL may already be the deepest entity, OR data is loaded")
                print("     dynamically (check for GQL/API). Upward traversal is possible")
                print("     but not recommended — inform the user if you take it.")
            else:
                print(f"[depth {depth}] No further links found — depth {depth-1} is the deepest level.")
            break

        print(f"[depth {depth}] {len(candidates)} candidate(s):")
        for i, u in enumerate(candidates, 1):
            print(f"  {i:2}. {u}")

        top = candidates[0]
        out_file = out_dir / f"detail_depth{depth}.html"
        print(f"\n[depth {depth}] Fetching: {top}")
        detail_html = fetch_and_save(top, out_file)
        run_validate(out_file)

        detail_len = text_len(detail_html)
        delta = detail_len - current_len
        symbol = f"+{delta:,}" if delta >= 0 else f"{delta:,}"
        print(f"[depth {depth}] Content: {current_len:,} -> {detail_len:,} ({symbol} chars)", end="")

        if delta > 200:
            print("  ->richer data found, going deeper")
            deepest_depth = depth
            deepest_url = top
            current_html = detail_html
            current_url = top
            current_len = detail_len
        else:
            print("  ->no significant content gain, stopping here")
            if deepest_depth == 0:
                deepest_depth = depth
                deepest_url = top
            break

        print()

    print(f"\n[probe_detail] Deepest entity: depth={deepest_depth}, url={deepest_url}")
    if deepest_depth > 0:
        print(f"[probe_detail] Saved: {out_dir}/detail_depth{deepest_depth}.html")
    print(f"[probe_detail] Use this page for MODEL — map ALL fields visible on it.")


if __name__ == "__main__":
    main()
