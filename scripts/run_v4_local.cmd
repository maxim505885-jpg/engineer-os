@echo off
setlocal
set "ENGINEER_OS_USER_REPO=%~dp0..\..\engineer-os"
set "ENGINEER_OS_PYTHON=%ENGINEER_OS_USER_REPO%\.venv\Scripts\python.exe"
if not exist "%ENGINEER_OS_PYTHON%" (
  echo BLOCK: Python virtual environment missing: %ENGINEER_OS_PYTHON%
  exit /b 2
)
"%ENGINEER_OS_PYTHON%" "%~dp0run_v4_local.py"
exit /b %ERRORLEVEL%
