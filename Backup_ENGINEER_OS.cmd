@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
title ENGINEER OS Data Backup
set "PY=.venv\Scripts\python.exe"
if exist "%PY%" goto run
where py >nul 2>&1 || (
  echo Python was not found.
  pause
  exit /b 2
)
set "PY=py -3.13"
:run
%PY% scripts\backup_engineer_os_data.py
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" pause
exit /b %RC%
