books.toscrape.com
==================

Dumps the full catalogue of books.toscrape.com (a public sandbox built for scraping
practice) to books.csv + books.xlsx.

HOW TO RUN
----------
1. One-time, from the ScrapBuilder root: create the shared venv
   (py -3.12 -m venv .venv  then  .venv\Scripts\python -m pip install -r requirements.txt)
2. Double-click run.bat.
3. Open books.csv or books.xlsx.

Full run = 50 listing pages + ~1000 detail pages (~10 min at the polite 0.5s rate).
Options: run.bat --max-pages 2 (quick slice), run.bat --no-detail (listing only, fast).

COLUMNS
-------
title, category, rating (1-5), price_incl, price_excl, tax, availability, stock_qty,
upc, num_reviews, description, product_url, image_url.

HOW IT WORKS
------------
Archetype B+C, Tier 2 (static server-rendered HTML - no API, no JS rendering needed).
scripts/parse.py reads each listing card, then enriches it from the book's detail page.
Polite: respects robots.txt, identifiable User-Agent, 0.5s rate limit, retry/backoff.
