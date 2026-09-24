@echo off
setlocal
title ENGINEER OS - One Click Start

cd /d "%~dp0.."

echo.
echo ==========================================
echo        ENGINEER OS - ONE CLICK START
echo ==========================================
echo.

if not exist "%CD%\scripts\local_openwebui_smoke.py" (
  echo [ERROR] ENGINEER OS files are missing.
  pause
  exit /b 1
)

echo [1/4] Checking Open WebUI...
powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8080/' -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 (
  echo [INFO] Open WebUI is not running. Starting it...
  start "Open WebUI" powershell -NoExit -ExecutionPolicy Bypass -Command "$env:DATA_DIR='C:\open-webui\data'; uvx --python 3.11 open-webui@latest serve"
  echo Waiting for Open WebUI...
  powershell -NoProfile -Command "$ok=$false; 1..60 | %% { try { Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8080/' -TimeoutSec 2 | Out-Null; $ok=$true; break } catch {}; Start-Sleep -Seconds 2 }; if ($ok) { exit 0 } else { exit 1 }"
  if errorlevel 1 (
    echo [ERROR] Open WebUI did not become available.
    pause
    exit /b 1
  )
)

echo [2/4] Configuring ENGINEER OS runtime...
set "PYTHONPATH=%CD%"
set "ENGINEER_OS_OPEN_WEBUI_URL=http://127.0.0.1:8080"

if "%ENGINEER_OS_OPEN_WEBUI_MODEL%"=="" set "ENGINEER_OS_OPEN_WEBUI_MODEL=gemini-3-flash-preview"

if "%ENGINEER_OS_OPEN_WEBUI_API_KEY%"=="" (
  echo.
  echo Open WebUI requires an API key for ENGINEER OS.
  echo Enter it once for this Windows process.
  set /p "ENGINEER_OS_OPEN_WEBUI_API_KEY=Open WebUI API key: "
)

if "%ENGINEER_OS_OPEN_WEBUI_API_KEY%"=="" (
  echo [ERROR] No Open WebUI API key supplied.
  pause
  exit /b 1
)

echo [3/4] Checking ENGINEER OS local runtime...
python scripts/local_openwebui_smoke.py
if errorlevel 1 (
  echo.
  echo ==========================================
  echo ENGINEER OS local runtime FAILED.
  echo ==========================================
  echo.
  pause
  exit /b 1
)

echo.
echo [4/4] RESULT
echo ==========================================
echo Open WebUI runtime: PASSED
echo Model: %ENGINEER_OS_OPEN_WEBUI_MODEL%
echo ENGINEER OS transport: PASSED
echo Engineering status is reported by the smoke test.
echo ==========================================
echo.
pause
endlocal
