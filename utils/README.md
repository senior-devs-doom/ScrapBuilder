# utils/ — builder-side helpers

Scripts the **agent** uses while building. These are NOT shipped inside `apps/` and are
not part of any crawler the user runs.

- `discovery.py` — SCOUT-phase reconnaissance: characterize a target, hunt for hidden
  JSON endpoints, read robots/sitemap. `python utils/discovery.py <url>`

Add probes here as you build a reusable discovery toolkit (record this in TOOLS.md).
