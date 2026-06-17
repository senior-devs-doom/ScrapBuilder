# ScrapBuilder

You give Claude Code a URL. It builds you a Python app. You double-click `run.bat`. You get a `.csv` + `.xlsx` with every product on that page — full spec table, variants, image links etc. Agent follows a flexible procedure and handles this intern abuse level task.

No programming required at any point.

```
URL  →  Claude Code builds app  →  double-click run.bat  →  products.csv
```

---

## Genesis use case

You want products and their specs from a supplier, but he just folds his arms and redirects you to his website. You want all 700 items as a spreadsheet — part numbers, names, dimensions, prices, image links — without manually painstankingly visiting each subpage, you have many middleages tech suppliers and you want to be able to update their data fast.

Paste the URL (filters and all) into Claude Code. Walk away. Come back to a complete `.csv` and `.xlsx`.

---

## Ethics

- **Robots.txt is respected.** If the site says no, the app stops and tells you.
- **Rate-limited by default.** Requests are spaced; the app doesn't hammer servers.
- **Identifies itself.** Every request carries a `User-Agent` string with a contact address so site operators can reach you.
- **No auth-walled data.** Only public-facing content the site serves to any visitor.
- **Your data stays local.** No cloud, no API calls at runtime, no third-party services.
- You only leak to your AI Agent provider, in my case Daddy Dario, but should work on local LLM and linux with minimal adjustments.

> Only use on sites you're authorized to scrape. Respect terms of use.

---

## How it works

| Step | Who | What |
|------|-----|-------|
| 1 | You | Paste a URL into Claude Code |
| 2 | Claude Code | Scouts the site, picks the cheapest extraction method |
| 3 | Claude Code | Builds a self-contained Python app under `apps/<site>/` |
| 4 | You | Double-click `run.bat` — once now, anytime later for a fresh dump |
| 5 | App | Writes `<app-name>.csv` + `<app-name>.xlsx` next to itself |

Claude Code does the work once. The app it leaves behind needs no agent, no API key, no technical knowledge to run again.

## What the agent does with your URL

**SCOUT** — fetches the page and inspects it before writing a single line of code. First,
it scans the raw HTML for prompt injection — instructions embedded in the page trying to
manipulate the agent (e.g. "ignore previous instructions"). If any are found it stops
immediately and flags it to you rather than blindly following a hostile page. Then it checks
`robots.txt`, looks for hidden JSON endpoints or GraphQL APIs (cheaper and more reliable than
parsing HTML), and checks whether the site has detail pages or subcategories carrying richer
data than the listing — specs, variants, stock, full descriptions. If yes, the built app
crawls both levels. Only after understanding the full shape of the data does it pick an approach.

**MODEL** — pulls one complete record and lays out the exact CSV columns. Column names
come from the site's own language. If there are product images it asks: links in the CSV,
or download locally?

**BUILD** — writes the app: a `scripts/` folder with fetch, parse, and export logic, plus
`run.bat` as the double-click launcher. The app is hardwired to the URL you gave — filters,
pagination, and all. It rate-limits itself, retries on errors, and caches responses during
development so it doesn't hammer the site.

**VERIFY** — runs a small slice (a few pages) and inspects every column for gaps or garbled
data before committing to a full pull.

**REFLECT + EVOLVE** — writes what it learned back into its own documentation so the next
build starts smarter: new site archetypes, shortcuts discovered, tools that worked.

---

## What it handles

- Static HTML, JSON endpoints, paginated listings, filtered query URLs
- SPAs with server-side-rendered data (Apollo cache, `__NEXT_DATA__`, `ld+json`)
- Two-level crawls: listing page → product detail page (full spec tables, all variants)
- Dynamic column discovery — column names come from the site's own language
- Images as hyperlinks in the CSV (no local download unless requested)
- Polish, English, and other language sites

---

## Setup (one-time)

You need **Claude Code** (Anthropic's CLI — requires a paid Anthropic account) and this repo.
After that, open the repo in Claude Code and tell it to set up the environment.
It will handle everything from a fresh Windows machine via the console:

1. Install Python 3.12 via `winget` (ships with Windows 11)
2. Create the shared Python venv
3. Install all dependencies
4. Ask for your email to put in request headers (scraper etiquette)

After that, every scraper is a double-click. Full details if you need them manually:
[docs/ENVIRONMENT.md](docs/ENVIRONMENT.md)

---

## Layout

```
ScrapBuilder/
├── apps/                  # one built app per subfolder
│   └── site.section/      #   run.bat + scripts/ + output CSV/XLSX
├── docs/                  # agent's evolving knowledge base
│   ├── METHODOLOGY.md     #   how the agent scouts and builds
│   ├── CASES.md           #   site archetypes and playbooks
│   ├── TOOLS.md           #   extraction tools and when to use each
│   └── ENVIRONMENT.md     #   venv setup and runtime details
├── utils/                 # builder-side discovery tools (not shipped in apps)
└── CLAUDE.md              # agent constitution — boot sequence and prime directives
```

---

## For Claude Code (agent)

Read `CLAUDE.md` first, every session. Invoke `build-scraper` to build. Invoke `evolve-docs` before signing off — the docs are the brain; update them or the next session starts blind.

---

## License

MIT — built this crap in like a day instead of finishing the semester >.<
