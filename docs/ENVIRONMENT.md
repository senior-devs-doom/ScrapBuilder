# Environment

**One shared venv for everything** — the builder and every app it generates run from the
same `.venv`. Decided 2026-06-17 for lowest upkeep (see [JOURNAL.md](JOURNAL.md) Session 1).

## Agent-driven setup (fresh Windows)

When the agent detects the venv is missing or Python 3.12 isn't present, it runs this
sequence via PowerShell before doing anything else:

### 1. Check Python 3.12
```powershell
py -3.12 --version
```
If that errors: install it. `winget` ships with Windows 11 by default.
```powershell
winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
```
After install, open a new PowerShell window (PATH update requires a fresh shell) and
confirm with `py -3.12 --version`.

### 2. Create the venv
```powershell
py -3.12 -m venv .venv
```

### 3. Install dependencies
```powershell
.venv\Scripts\python -m pip install -r requirements.txt
```

### 4. Create creds.txt
Check if `creds.txt` exists at the project root. If not, ask the user for their email
and write it:
```
contact=user@email.com
```
Apps use this in the `User-Agent` header so site operators can identify the requester.
If the file is absent apps still run; the contact field is silently omitted.

### Health check
After setup, verify the venv works:
```powershell
.venv\Scripts\python -c "import requests, openpyxl; print('OK')"
```

---

## The setup (steady state)
- **Interpreter: Python 3.12** — not 3.14, see "Why 3.12" below.
- **venv:** `.venv/` at the project root.
- **Deps:** single root [requirements.txt](../requirements.txt) covers builder + apps.

### Use it
- Agent/builder: call `.venv\Scripts\python ...` (or activate the venv).
- Generated apps: each ships a `run.bat` that invokes `..\..\.venv\Scripts\python scripts\main.py`
  so a double-click uses the shared venv regardless of Windows file associations.
- VS Code: Command Palette → "Python: Select Interpreter" → pick `.venv`.

## Why 3.12, not 3.14
3.14 is bleeding-edge; the ecosystem lags on **compiled** wheels for it. On 3.14,
`selectolax` would not install (no wheel) and Tier-4 `playwright` was a risk. On 3.12
every package — including `selectolax` and `playwright` — has wheels. 3.12 is the current
maturity sweet spot: broadest compatibility, least breakage. System default stays 3.14;
we just point the venv at the already-installed 3.12.

## Tradeoff we accepted
Apps are **not portable off this machine** — they rely on the shared venv, not a per-app
`requirements.txt`. That was the explicit choice for simplicity/upkeep. If an app ever
needs to ship elsewhere, generate a per-app `requirements.txt` from the imports it uses
and revert it to the standalone model.

## Installed core (pinned in requirements.txt)
requests, httpx, extruct, jmespath, beautifulsoup4 (+soupsieve), lxml, requests-cache,
pandas, openpyxl, selectolax.
playwright is install-on-demand (heavy; also needs `playwright install chromium`).
