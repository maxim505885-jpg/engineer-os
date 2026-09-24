@echo off
setlocal
title ENGINEER OS - Local Launcher

cd /d "%~dp0.."

echo.
echo ==========================================
echo        ENGINEER OS LOCAL LAUNCHER
echo ==========================================
echo.

if not exist "%CD%\scripts\local_openwebui_smoke.py" (
  echo [ERROR] ENGINEER OS files are missing.
  pause
  exit /b 1
)

echo [1/4] Checking Ollama...
where ollama >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Ollama is not installed or not in PATH.
  echo Install Ollama, then run this launcher again.
  pause
  exit /b 1
)

ollama list | findstr /I /C:"qwen3:8b" >nul 2>&1
if errorlevel 1 (
  echo [INFO] qwen3:8b is not installed.
  echo Pulling qwen3:8b...
  ollama pull qwen3:8b
  if errorlevel 1 (
    echo [ERROR] Failed to install qwen3:8b.
    pause
    exit /b 1
  )
)

echo [2/4] Checking Open WebUI...
powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8080/' -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 (
  echo [INFO] Open WebUI is not running.
  echo Starting Open WebUI in a separate window...
  start "Open WebUI" powershell -NoExit -ExecutionPolicy Bypass -Command "$env:DATA_DIR='C:\open-webui\data'; uvx --python 3.11 open-webui@latest serve"
  echo Waiting for Open WebUI...
  powershell -NoProfile -Command "$ok=$false; 1..60 | %% { try { Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8080/' -TimeoutSec 2 | Out-Null; $ok=$true; break } catch {}; Start-Sleep -Seconds 2 }; if ($ok) { exit 0 } else { exit 1 }"
  if errorlevel 1 (
    echo [ERROR] Open WebUI did not become available on http://127.0.0.1:8080
    pause
    exit /b 1
  )
)

echo [3/4] Configuring ENGINEER OS...
set "PYTHONPATH=%CD%"
set "ENGINEER_OS_OPEN_WEBUI_URL=http://127.0.0.1:8080"
set "ENGINEER_OS_OPEN_WEBUI_MODEL=qwen3:8b"

if "%ENGINEER_OS_OPEN_WEBUI_API_KEY%"=="" (
  echo.
  echo API key is required by your Open WebUI installation.
  echo Enter it below. The key is used only for this Windows process.
  echo It is NOT written to ENGINEER OS or GitHub.
  set /p "ENGINEER_OS_OPEN_WEBUI_API_KEY=Open WebUI API key: "
)

if "%ENGINEER_OS_OPEN_WEBUI_API_KEY%"=="" (
  echo [ERROR] No API key supplied.
  pause
  exit /b 1
)

echo [4/4] Running ENGINEER OS smoke test...
echo.
python scripts/local_openwebui_smoke.py

if errorlevel 1 (
  echo.
  echo ==========================================
  echo ENGINEER OS smoke test FAILED.
  echo ==========================================
  echo.
  pause
  exit /b 1
)

echo.
echo ==========================================
echo ENGINEER OS smoke test PASSED.
echo ==========================================
echo.
pause
endlocal
