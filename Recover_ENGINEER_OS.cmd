@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title ENGINEER OS - Data Recovery
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -X utf8 "scripts\run_data_recovery.py"
) else (
  where py >nul 2>&1
  if not errorlevel 1 (
    py -3 -X utf8 "scripts\run_data_recovery.py"
  ) else (
    python -X utf8 "scripts\run_data_recovery.py"
  )
)
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" pause
exit /b %RC%
