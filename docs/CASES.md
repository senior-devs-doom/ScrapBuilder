# Site Archetypes & Playbooks

A living catalogue. Each session, if you meet a site that doesn't fit, add an archetype.
If you refine a playbook, edit it in place. This is the institutional memory that makes
session N+1 faster than session N.

> Status: growing. Archetypes B (HTML listing) and G (Headless SPA + GQL) confirmed in
> the wild. Others remain theoretical until a JOURNAL entry validates them.

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
- **Find the endpoint:** Network tab → filter `graphql` → grab POST URL, `Origin`/`Referer`
  headers, and the operation name from the request body.
- **Read the bundled query file FIRST:** before probing, find the `.js` asset that contains
  the GQL operation (search by operation name). The query document inside gives correct
  field names, variable types, and nested arg patterns — authoritative, free, no roundtrips.
  Also attempt introspection: `{"query":"{__schema{types{name fields{name}}}}"}`. If enabled:
  full schema. If disabled: fall back to the bundle.
- **Identify the real data resolver:** GQL responses often have multiple sub-resolvers.
  The one backed by the search/discovery layer (variants, hits) is usually reliable; the one
  backed by a separate commerce platform (product detail enrichment) may return 404s per
  item — treat partial errors on non-critical fields as expected, not fatal.
- **Schema divergence:** JS bundle field names and the live schema can differ. Let GQL
  validation errors guide you — "Did you mean X?" is authoritative.
- **Nested variable pattern:** some field-level args require a variable declared at query
  level but NOT passed to the top-level resolver — only to the nested field selector.
  Example: `$locale: Locale!` used as `someField(lang: $locale)` not as a query argument.
- **Pagination:** integer `page` variable (1-based) + `quantity`. Stop when
  `len(hits) < quantity`.
- **Filter extraction from URL:** query-string keys starting with `filter` → strip prefix →
  filter field name. `urllib.parse.parse_qs` decodes encoded chars and `+`→space correctly.
- **Response list wrapping:** some fields return `[{...}]` not `{...}`. Always check type;
  take `[0]` when it's a list.
- **Channel/tenant ID pattern:** channel = `{site-prefix}-{locale}` derived from site
  config — check the main JS bundle for a `channel()` or `factFinderChannel()` function.
- **Apollo cache in HTML (free Tier 1 data):** SSR SPAs often inject the Apollo Client
  cache as a JSON blob in an inline `<script>` tag. Look for `"ROOT_QUERY"` in script
  text; `json.loads(tag.string)` gives the full cache. The `ROOT_QUERY` keys reveal every
  GQL operation the page fired and their full results — field names, types, nested data —
  without needing introspection or bundle analysis.
- **Two-level GQL detail for technical attributes:** If the listing resolver only returns
  summary fields (name, slug, image, category), check the Apollo cache of a product detail
  page for a second resolver (e.g. `getCatalogProductDataById`). That resolver may return
  `Attributes: [{AttributeKey, AttributeName, Value, Unit}]` with the full spec table.
  Probe it directly as a GQL query — note that locale params may use `CatalogLocale!`
  type, not `String!` (let validation errors guide you). Design the scraper as two-level:
  listing pass → detail pass per ID. Use `--no-detail` flag for fast listing-only VERIFY.
- **Dynamic attribute columns:** When detail attributes vary by product type, collect all
  attribute keys across the full dataset before writing the CSV (two-pass: list all IDs,
  then fetch details, then write). Use `AttributeName` (HTML-stripped) as the column
  header. Sparse columns (genuinely optional per product type) are expected — verify with
  `check_coverage.py`.

---

## Cross-cutting gotchas (add as you hit them)
- **Pagination — scout before assuming:** not all listing pages paginate. Check first. When
  pagination exists, prefer an explicit next-link or total over "until empty"; always cap
  with MAX_PAGES so a bad loop can't run forever.
- **GQL schema vs JS bundle field names may differ:** The JS bundle is bundled at build time
  and may reference fields that were renamed in the live schema. Always confirm field names
  via GQL validation errors (the server's "Did you mean X?" messages are authoritative).
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
