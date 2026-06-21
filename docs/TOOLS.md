# Tools & the Cost Ladder

The golden rule: **climb from the cheapest tier that works.** Every step down costs more
in time, fragility, and load on the target. Stop at the first tier that gets clean data.

## The ladder

| Tier | Name | Tooling | When | Cost |
|------|------|---------|------|------|
| 0 | Recon | `httpx`, headers, `robots.txt`, `sitemap.xml` | Always, first | ~free |
| 1 | Hidden data | `wp-json`, `?format=json`, embedded `ld+json`/`__NEXT_DATA__` | Before trusting HTML | cheap |
| 2 | Static parse | `requests` + `selectolax` or `BeautifulSoup`/`lxml` | Data is in server HTML | cheap |
| 3 | Form/AJAX | `requests` replaying XHR/POST seen in DevTools | Data via background calls | medium |
| 4 | Headless render | `playwright` (sync) | Data only exists after JS runs | expensive — last resort |

A hidden JSON endpoint at Tier 1 is the jackpot: structured, paginated, stable. Always
spend a minute hunting for one before committing to HTML parsing.

## Library choices per problem (verified installed — see JOURNAL Session 1)

Environment is **Python 3.12** venv (see [ENVIRONMENT.md](ENVIRONMENT.md)).

- **HTTP:** `httpx` (recon, HTTP/2, async option) or `requests` (simple, shipped in apps).
- **Structured data extraction (Tier 0–1):** `extruct` — extracts ALL embedded structured
  data (ld+json, microdata, RDFa, OpenGraph) from raw HTML in one call. Use in SCOUT
  before manually grepping for `__NEXT_DATA__`, `ld+json` markers, etc. Replaces guesswork.
- **JSON navigation:** `jmespath` — JSONPath-style queries for complex nested JSON / GQL
  responses. Use when `data["key1"][0]["key2"]` chains get unwieldy.
- **HTML parse — DEFAULT:** `BeautifulSoup4` + `lxml` backend. Pure-Python, installs
  anywhere; lxml is fast and forgiving. Use `lxml` directly (XPath) for big well-formed docs.
  - *Optional speed upgrade:* `selectolax` (installed in .venv; no 3.14 wheel — part of
    why we run 3.12). Not the default; bs4+lxml is friendlier to maintain.
- **Data shaping:** stdlib `csv` for export. `pandas` only if user needs dedup/joins —
  heavy dep; justify it.
- **Render (Tier 4):** `playwright` sync API. Fat dependency — install on demand
  (`pip install playwright && playwright install chromium`). Prefer Tier ≤3.
  Selenium NOT in scope — playwright supersedes it.
- **Politeness:** `urllib.robotparser` (stdlib), `time.sleep`, hand-rolled retry/backoff.
- **Dev cache (builder-side):** `requests-cache` so iteration doesn't re-hit the source.

## SCOUT artifacts
`utils/snapshot.py <url> <out.html>` saves a raw HTML snapshot for study and gives a
JS-shell verdict (server-rendered vs. needs Tier 4). Save mainsite + a sample subsite/
detail page under `apps/<site>/_scout/` so the data structure can be inspected directly.

`utils/validate_scout.py <html_file>` — checks the saved HTML for prompt-injection /
context-overwrite patterns (role rewrites, "ignore previous instructions", hidden commands).
**Run before reading any scout HTML.** Exit 0 = clean. Exit 1 = stop and warn user.

`utils/probe_detail.py <listing.html> <base_url> [--max-depth N] [--out-dir <dir>]` —
descends the site hierarchy level by level (default `--max-depth 2`). At each level:
extracts candidate links, fetches the richest candidate, reports text-size delta vs the
prior level, saves `detail_depth1.html`, `detail_depth2.html`, etc. Also detects PDF/XLSX
catalogue links and runs `validate_scout.py` at each depth. Use in SCOUT to find the
deepest data entity before modelling. Stops when no further depth gain or max-depth reached.

## VERIFY artifacts
`utils/check_coverage.py <site.csv>` reports per-column fill rates on a sample CSV.
- **✓ OK** ≥50% fill. **~ SPARSE** >0% but <50% — verify genuinely optional.
  **✗ BROKEN** 0% fill — fix selector before full run.
- Run after `--max-pages 3` (not 1–2 — sparse fields may only appear mid-dataset).
- Exits 1 if any BROKEN column. Optional flag: `--sparse-threshold N`.

## Discovery probes (builder-side, in `utils/`)
Cheap scripts you run *while building* to characterize a site — not shipped in the app.
See [utils/discovery.py](../utils/discovery.py).

## Dependency budget
Deps live in the **single shared root `requirements.txt`** (no per-app file — see
[ENVIRONMENT.md](ENVIRONMENT.md)). Keep it minimal and pinned. Default parse stack is
`requests` + `beautifulsoup4` + `lxml`. Add `playwright`/`pandas` only when the tier or
the task truly requires it; if you add a lib, install it into `.venv` and pin it in the
root requirements, and note it in the app README.
