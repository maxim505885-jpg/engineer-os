@echo off
set "LIRA_RESULTS_PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe" set "LIRA_RESULTS_PS=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
"%LIRA_RESULTS_PS%" -NoProfile -STA -ExecutionPolicy Bypass -File "%~dp0RESULTS.ps1"
pause
