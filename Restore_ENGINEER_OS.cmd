@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
title ENGINEER OS Data Restore
set "BACKUP=%~1"
if not defined BACKUP (
  set /p "BACKUP=Full path to ENGINEER OS backup ZIP: "
)
if not defined BACKUP exit /b 2
set "TARGET=%~2"
if not defined TARGET (
  set /p "TARGET=New absent data directory for restore: "
)
if not defined TARGET exit /b 2
set "PY=.venv\Scripts\python.exe"
if exist "%PY%" goto run
where py >nul 2>&1 || (
  echo Python was not found.
  pause
  exit /b 2
)
set "PY=py -3.13"
:run
%PY% scripts\restore_engineer_os_data.py "%BACKUP%" "%TARGET%"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" pause
exit /b %RC%
