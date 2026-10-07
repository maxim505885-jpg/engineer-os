@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title ENGINEER OS Repository Backup
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\backup_repository.ps1"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" pause
exit /b %RC%
