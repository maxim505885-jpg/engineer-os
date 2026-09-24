@echo off
setlocal EnableExtensions
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

echo [1/5] Checking Open WebUI...
powershell -NoProfile -Command "try { $r=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8080/' -TimeoutSec 5; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { exit 0 } else { exit 1 } } catch { exit 1 }"
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

echo [2/5] Configuring ENGINEER OS runtime...
set "PYTHONPATH=%CD%"
set "ENGINEER_OS_OPEN_WEBUI_URL=http://127.0.0.1:8080"
if "%ENGINEER_OS_OPEN_WEBUI_MODEL%"=="" set "ENGINEER_OS_OPEN_WEBUI_MODEL=gemini-3-flash-preview"

if "%ENGINEER_OS_OPEN_WEBUI_API_KEY%"=="" (
  echo.
  echo Open WebUI API key is required.
  echo The key is hidden while you type and is used only for this process.
  powershell -NoProfile -Command "$p=Read-Host 'Open WebUI API key' -AsSecureString; $b=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($p); try { [Environment]::SetEnvironmentVariable('ENGINEER_OS_OPEN_WEBUI_API_KEY',[Runtime.InteropServices.Marshal]::PtrToStringBSTR($b),'Process') } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }"
)

if "%ENGINEER_OS_OPEN_WEBUI_API_KEY%"=="" (
  echo [ERROR] No Open WebUI API key supplied.
  pause
  exit /b 1
)

echo [3/5] Checking Open WebUI API...
powershell -NoProfile -Command "$h=@{Authorization='Bearer ' + $env:ENGINEER_OS_OPEN_WEBUI_API_KEY}; try { $r=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8080/api/models' -Headers $h -TimeoutSec 10; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { Write-Host ('[ERROR] Open WebUI API check failed: ' + $_.Exception.Message); exit 1 }"
if errorlevel 1 (
  echo [ERROR] Open WebUI API is not accepting the supplied key or connection.
  echo Check Open WebUI Settings ^> Account/Settings ^> API Keys.
  pause
  exit /b 1
)

echo [4/5] Running ENGINEER OS local runtime...
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
echo [5/5] RESULT
echo ==========================================
echo Open WebUI API: PASSED
echo Model: %ENGINEER_OS_OPEN_WEBUI_MODEL%
echo ENGINEER OS runtime: PASSED
echo Engineering status is reported by the smoke test.
echo ==========================================
echo.
pause
endlocal
