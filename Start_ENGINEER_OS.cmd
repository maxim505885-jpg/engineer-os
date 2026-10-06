@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title ENGINEER OS
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows_supervisor.ps1"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo Startup failed. See .engineer-os\logs\windows-supervisor.log
  pause
)
exit /b %RC%
