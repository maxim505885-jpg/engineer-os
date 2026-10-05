@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>nul
  if not errorlevel 1 (
    ".venv\Scripts\python.exe" scripts\run_local_app.py
    goto finished
  )
)
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>nul
if not errorlevel 1 (
  py -3 scripts\run_local_app.py
  goto finished
)
python -c "import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>nul
if not errorlevel 1 (
  python scripts\run_local_app.py
  goto finished
)
echo Python 3.12 or newer is required. Your installed Python 3.13 or 3.14 is supported.
echo Install Python from https://www.python.org/downloads/windows/
:finished
pause
endlocal
