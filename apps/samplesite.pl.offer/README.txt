samplesite.pl.offer — TEMPLATE
==============================

This is the non-functional template that every ScrapBuilder app is copied from.
The builder agent fills in scripts/fetch.py and scripts/parse.py for the real target.

HOW TO RUN
----------
1. One-time, from the ScrapBuilder root: create the shared venv
   (py -3.12 -m venv .venv  then  .venv\Scripts\python -m pip install -r requirements.txt)
2. Double-click run.bat.
3. Open <site>.csv or <site>.xlsx.

HOW IT WORKS
------------
scripts/main.py  - orchestrates fetch -> parse -> export
scripts/fetch.py - HTTP/session, retries, rate-limit, dev cache
scripts/parse.py - one record HTML/JSON -> dict (the fragile part; keep it isolated)
scripts/export.py - list[dict] -> CSV + XLSX (stable column order, utf-8-sig)
run.bat          - double-click launcher; uses the shared project venv (Python 3.12)
