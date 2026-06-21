# ScrapBuilder — Manifest

**What:** An agent-assisted framework that manufactures bespoke procedural web crawlers,
one per target URL, in Python.

**Why:** Some sites expose a useful dataset only through their (often old, low-tech
PHP/WordPress) front-end — no API. ScrapBuilder turns "here's a link" into "here's a
folder that dumps the dataset behind that link to CSV on a double-click."

**Input:** A single URL, from the user, to the agent. It may be a homepage, a subpage, or
a filtered query URL with query-string params (e.g. `site.com/products?filterColor=blue`).
The given URL — filters included — defines the scope; the target is never assumed to be a root.

**Output:** `apps/<site>/` containing `run.bat` (launcher), `main.py`, a `scripts/`
package, and a fresh `<site>.csv` produced by running it.

**Hard constraints:**
- Built apps need no agent and no API key at runtime — never call Anthropic. They DO run
  from the shared project venv (Python 3.12), so they are not portable off this machine.
  That tradeoff was chosen for upkeep — see [ENVIRONMENT.md](ENVIRONMENT.md).
- Climb the cost ladder: hidden API > static HTML parse > headless render.
- Polite scraping: robots.txt, User-Agent, rate limits, dev-time caching.
- One app per session; the agent reports laconically after each step.

**Out of scope:** Sites with a real API (use the API), auth-walled/paywalled content,
anything the user isn't authorized to scrape, JS-game-level interactivity.

**Status:** Session 14. Five apps: Tier 1 Plone custom AJAX+JSON (×1), Tier 1 Drupal
JSON:API (×1), Tier 2 HTML listing (×1), Tier 3 GQL SPA (×2 two-level dynamic columns).
Current state always in [JOURNAL.md](JOURNAL.md).
