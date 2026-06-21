# Site Archetypes & Playbooks

A living catalogue. Each session, if you meet a site that doesn't fit, add an archetype.
If you refine a playbook, edit it in place. This is the institutional memory that makes
session N+1 faster than session N.

> Status: growing. Archetypes B (HTML listing), G (Headless SPA + GQL), H (Drupal JSON:API),
> and I (Plone CMS custom endpoints) confirmed in the wild. Others remain theoretical.

---

## A. WordPress (REST API present)
**Tells:** `/wp-json/` responds, `wp-content/` in asset URLs, `X-Powered-By`, generator meta.
**Playbook:** Skip the HTML entirely. Hit `/wp-json/wp/v2/<type>?per_page=100&page=N`.
Paginate via the `X-WP-TotalPages` header. Custom post types live at custom routes —
GET `/wp-json/` to list them. Tier 1. Usually the easiest possible win.

## B. Listing page (cards/rows)  *(CONFIRMED — books.toscrape.com, Session 4)*
**Tells:** repeating card/row grid — each card links to or contains one data record.
Pagination is common but not universal; a listing may show all records on a single page.
**Playbook:** Tier 2.
- **Scout traversal first** — do not assume pagination exists. Look for: a next-link, a
  "Page X of Y" counter, a `?page=N` / `?start=N` param, or nothing (single page).
- **Single-page listing:** one fetch, parse all cards, done. No loop needed.
- **Paginated listing:** follow the mechanism found. Next-link absence is the cleanest stop
  signal when available (books.toscrape.com). Otherwise increment `?page=N` and stop on
  empty results. Always cap with MAX_PAGES against runaway loops.
**Two-level crawl (common):** the card is a *summary*; the full record lives on a
per-item **detail page**. Fetch listing → per card, fetch detail URL → merge.
Detail page is authoritative for precise fields (IDs, taxes, stock, descriptions).
Request budget ≈ pages + items — gate detail behind `--no-detail`, rate-limit.
Confirmed on books.toscrape.com (paginated + detail): card gives title/price/rating;
detail adds UPC, category, tax, stock_qty, reviews, description.

## C. Static HTML table
**Tells:** A `<table>` with `<thead>`/`<tbody>` holding the whole dataset on one page.
**Playbook:** Tier 2, trivial. `<th>` → columns, `<tr>` → rows. Watch for multi-page tables
(falls back to archetype B).

## D. AJAX / hidden JSON endpoint
**Tells:** Page looks empty in raw HTML but full in browser; DevTools Network shows
`/api/…`, `admin-ajax.php`, or XHR returning JSON.
**Playbook:** Tier 3. Replay the XHR with `requests` (copy headers/params, often a POST).
Frequently exposes cleaner, paginated data than the HTML ever would.

## E. JS-rendered SPA (no usable hidden endpoint)
**Tells:** Raw HTML is a near-empty shell + JS bundle; no JSON endpoint findable; framework
markers (`__NEXT_DATA__` absent or obfuscated).
**Playbook:** Tier 4, `playwright`. Render, wait for the data selector, then parse the DOM
or intercept network responses. Fat dependency — confirm tiers 0–3 truly failed first.

## F. File-based dumps
**Tells:** The "database" is actually downloadable files (CSV/XLSX/PDF) linked from a page.
**Playbook:** Tier 1–2. Scrape the list of file links, download, normalize each into rows.
No record-level HTML parsing needed — just file discovery + a per-format reader.

## G. Headless CMS SPA + proprietary GraphQL proxy  *(CONFIRMED — Session 9)*
**Tells:** Raw HTML is a near-empty CMS/SPA shell (Next, Nuxt, Vue, Sitecore, etc.).
DevTools shows GQL POST to a `/graphql*` endpoint, often on a **different domain** than
the site. Products never appear in the HTML source.
**Playbook:** Tier 3. Replay the GQL POST — no browser needed.
- **Read the bundled query file FIRST:** find the `.js` asset containing the GQL operation
  (search by operation name). Gives correct field names, variable types, nested args —
  authoritative, free. Also try introspection; if disabled, fall back to the bundle.
- **Identify the real data resolver:** GQL responses often have multiple sub-resolvers.
  The search/discovery one (variants, hits) is reliable; the commerce-platform one (detail
  enrichment) may return 404s per item — treat partial errors on non-critical fields as
  expected, not fatal.
- **Nested variable pattern:** some field-level args require a variable at query level
  but passed only to the nested field selector, not the top-level resolver.
- **Pagination:** integer `page` variable (1-based) + `quantity`. Stop when
  `len(hits) < quantity`.
- **Filter extraction from URL:** query-string keys starting with `filter` → strip prefix →
  filter field name. `urllib.parse.parse_qs` decodes encoded chars and `+`→space correctly.
- **Apollo cache in HTML (free Tier 1 data):** SSR SPAs inject the Apollo cache as inline
  JSON (`"ROOT_QUERY"` key). `json.loads(tag.string)` reveals every GQL operation fired and
  its full results — field names, types, nested data — no introspection roundtrip needed.
- **Two-level GQL detail for technical attributes:** If listing resolver returns summaries
  only, check the detail page Apollo cache for a second resolver returning `Attributes:
  [{AttributeKey, AttributeName, Value, Unit}]`. Locale params may use `CatalogLocale!`
  not `String!` — let validation errors guide you. Use `--no-detail` for fast VERIFY.
- **Dynamic attribute columns:** Two-pass: list all IDs → fetch details → collect all
  `AttributeName` keys (HTML-stripped) → write CSV. Sparse per-type columns expected;
  `check_coverage.py` verifies.

## H. Drupal JSON:API  *(CONFIRMED — Session 13)*

**Tells:** `/jsonapi/` returns `application/vnd.api+json`; `X-Generator: Drupal` in headers.
**Playbook:** Tier 1. GET `/jsonapi/` → lists all resource types. Filter by relationship
UUID: `?filter[field_*_rel_*.id]=<uuid>` — always read one entity's `relationships` keys
for the exact field name before writing any filter (never guess). Include chain:
`?include=rel1,rel2.subrel`. Pagination: `page[offset]` + `page[limit]`; stop when
`"next"` absent from `links`. Spec tables may be HTML fields: check `data-nb-cols` for
authoritative leaf-column count before building a rowspan/colspan solver; row values may
be `#//#`-delimited (first cell = variant code). path.alias CONTAINS filter returns 500 —
match locally. Sparse columns across entity subtypes are expected and correct.

## I. Plone CMS  *(CONFIRMED — Session 14)*
**Tells:** `++plone++` in asset URLs (e.g. `/++plone++<pkg>/scripts/`). REST API
(`/@search`, `/@types`) may return 404 — not always exposed.
**Playbook:** Tier 1. Skip REST probes. Grep `app.min.js` for `.load(` and `.get(` —
each hit reveals a custom AJAX traverser URL. Listing: `GET <path>/<endpoint>?filter=X`
→ HTML fragment. Per-record: `GET <record_url>/<endpoint>` → JSON (often `Content-Type:
text/plain` despite JSON body — use `get()` + `json.loads()`). Repeated GET filter params
→ use `list[tuple]` with `urlencode`, not `dict`. Response field format: `{identifier,
type, display_value, value}` — always use `display_value`. Boolean `display_value` values
need string conversion before writing CSV.

---

## Cross-cutting gotchas (add as you hit them)
- **Always traverse to the deepest entity before modelling.** The listing is a summary.
  The full schema lives on the detail page — or the sub-detail page, or a catalogue
  document. Use `probe_detail.py --max-depth 2` to find it. If you model from the listing
  alone you will miss fields. Upward traversal (going UP the URL hierarchy) is a last
  resort — tell the user when you do it.
- **Pagination — scout before assuming:** not all listing pages paginate. Check first. When
  pagination exists, prefer an explicit next-link or total over "until empty"; always cap
  with MAX_PAGES so a bad loop can't run forever.
- **API field names: read before guessing.** For GQL: let validation errors guide you ("Did
  you mean X?" is authoritative). For REST/JSON:API: read one entity's `attributes` and
  `relationships` keys — the correct filter path is right there; don't guess field names.
- **Session summaries can be wrong about saved files:** A summary claiming a file contains
  data X is only as reliable as the last actual write. Always `Read` the file before
  trusting a summary's description of its contents. (Confirmed Session 9.)
- **Encoding (source):** Polish/PL sites are often Windows-1250 or mislabeled UTF-8 —
  verify, set explicitly when writing CSV (template writes `utf-8-sig` for Excel-PL).
- **Encoding (console):** Windows console is cp1250; `print()`-ing scraped £/€/non-ASCII
  data raises UnicodeEncodeError and kills an otherwise-fine run. Template `main.py` calls
  `sys.stdout.reconfigure(encoding="utf-8")` at startup — keep that in every app. (Confirmed
  Session 1.)
- **Anti-bot:** Cloudflare interstitials / 403 on default UA → set a real UA, slow down;
  if it persists, report to user rather than escalating to evasion.
- **Verify on a slice, not the whole site:** give crawlers a `--max-pages N` (and, for
  two-level crawls, `--no-detail`) flag so VERIFY runs in seconds against a handful of
  records instead of doing the full multi-thousand-request pull. (Confirmed Session 4.)
- **Rating/structured data in CSS classes:** values are sometimes encoded as class names
  (e.g. `class="star-rating Three"`) rather than text — read the class list, map to a value.
- **Preserve query-string filters when the entry URL is a filtered query** (e.g.
  `.../products?filterColor=blue`): that URL is the scope. When paginating, MERGE the page
  param into the existing query (`urllib.parse.parse_qs` → set `page` → `urlencode`),
  never overwrite the whole query string — or follow the site's own next-link, which already
  carries the filters. Watch encoding: non-ASCII and special chars in params must be
  percent-encoded correctly (`urlencode(..., quote_via=quote)`).
