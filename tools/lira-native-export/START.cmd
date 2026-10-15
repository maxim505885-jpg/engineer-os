@echo off
set "LIRA_EXPORT_PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe" set "LIRA_EXPORT_PS=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
"%LIRA_EXPORT_PS%" -NoProfile -STA -ExecutionPolicy Bypass -File "%~dp0EXPORT.ps1"
pause
