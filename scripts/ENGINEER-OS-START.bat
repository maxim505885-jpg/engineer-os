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
  for /f "delims=" %%K in ('powershell -NoProfile -Command "$p=Read-Host ''Open WebUI API key'' -AsSecureString; $b=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($p); try { $s=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($b); $bytes=[Text.Encoding]::UTF8.GetBytes($s); [Convert]::ToBase64String($bytes) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }"') do set "ENGINEER_OS_OPEN_WEBUI_API_KEY_B64=%%K"
)

if "%ENGINEER_OS_OPEN_WEBUI_API_KEY%"=="" if "%ENGINEER_OS_OPEN_WEBUI_API_KEY_B64%"=="" (
  echo [ERROR] No Open WebUI API key supplied.
  pause
  exit /b 1
)

echo [3/5] Checking Open WebUI API...
powershell -NoProfile -Command "$ErrorActionPreference='Stop'; try { if ($env:ENGINEER_OS_OPEN_WEBUI_API_KEY_B64) { $bytes=[Convert]::FromBase64String($env:ENGINEER_OS_OPEN_WEBUI_API_KEY_B64); $env:ENGINEER_OS_OPEN_WEBUI_API_KEY=[Text.Encoding]::UTF8.GetString($bytes).Trim() }; if (-not $env:ENGINEER_OS_OPEN_WEBUI_API_KEY) { throw 'Empty API key' }; if ($env:ENGINEER_OS_OPEN_WEBUI_API_KEY -match '[\x00-\x1F\x7F]') { throw 'API key contains control characters' }; $h=@{Authorization='Bearer ' + $env:ENGINEER_OS_OPEN_WEBUI_API_KEY}; $r=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8080/api/models' -Headers $h -TimeoutSec 10; if ($r.StatusCode -ne 200) { throw ('HTTP ' + $r.StatusCode) }; Write-Host '[OK] Open WebUI API accepted the key.' } catch { Write-Host ('[ERROR] Open WebUI API check failed: ' + $_.Exception.Message); exit 1 }"
if errorlevel 1 (
  echo [ERROR] Open WebUI API is not accepting the supplied key or connection.
  echo Check Open WebUI Settings ^> Account/Settings ^> API Keys.
  pause
  exit /b 1
)

echo [4/5] Running ENGINEER OS local runtime with Python 3.11...
where uv >nul 2>nul
if errorlevel 1 (
  echo [ERROR] uv is required to run the ENGINEER OS local runtime with Python 3.11.
  echo Install uv, then run this launcher again.
  pause
  exit /b 1
)
powershell -NoProfile -Command "if ($env:ENGINEER_OS_OPEN_WEBUI_API_KEY_B64) { $bytes=[Convert]::FromBase64String($env:ENGINEER_OS_OPEN_WEBUI_API_KEY_B64); $env:ENGINEER_OS_OPEN_WEBUI_API_KEY=[Text.Encoding]::UTF8.GetString($bytes).Trim() }; & uv run --python 3.11 python scripts/local_openwebui_smoke.py; exit $LASTEXITCODE"
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
echo ENGINEER OS runtime transport: PASSED
echo Engineering status: see JSON result above (UNCERTAINTY is expected for this no-materials smoke test).
echo ==========================================
echo.
pause
endlocal
