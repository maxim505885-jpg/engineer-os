@echo off
set "LIRA_PROBE_PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe" set "LIRA_PROBE_PS=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
"%LIRA_PROBE_PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0engineer_os_lira_api_probe.ps1"
pause
