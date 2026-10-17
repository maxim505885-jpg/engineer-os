@echo off
cd /d "%~dp0"
if exist ".venv-engineering\Scripts\python.exe" (
  ".venv-engineering\Scripts\python.exe" scripts\launch_spu_desktop.py %*
) else (
  python scripts\launch_spu_desktop.py %*
)
if errorlevel 1 pause
