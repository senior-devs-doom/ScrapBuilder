@echo off
REM ScrapBuilder app launcher — double-click this to run the crawler.
REM Uses the shared project venv (Python 3.12) regardless of system file associations.
setlocal
set "VENV_PY=%~dp0..\..\.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
  echo [!] Shared venv not found at "%VENV_PY%".
  echo     From the ScrapBuilder root, create it once:
  echo         py -3.12 -m venv .venv
  echo         .venv\Scripts\python -m pip install -r requirements.txt
  echo.
  pause
  exit /b 1
)
"%VENV_PY%" "%~dp0scripts\main.py" %*
echo.
echo === Finished. Your CSV + XLSX are in this folder. Press any key to close. ===
pause >nul
