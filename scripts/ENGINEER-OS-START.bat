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

echo [3/5] Checking Open WebUI API...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; try { $key=$env:ENGINEER_OS_OPEN_WEBUI_API_KEY; if ([string]::IsNullOrEmpty($key)) { Write-Host ''; Write-Host 'Open WebUI API key is required.'; Write-Host 'The key is hidden while you type and is used only inside this PowerShell process.'; $secure=Read-Host 'Open WebUI API key' -AsSecureString; $ptr=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure); try { $key=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) } }; $key=$key.Trim(); if ([string]::IsNullOrEmpty($key)) { throw 'Empty API key' }; $headers=@{Authorization=('Bearer ' + $key)}; $r=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8080/api/models' -Headers $headers -TimeoutSec 10; if ($r.StatusCode -ne 200) { throw ('HTTP ' + $r.StatusCode) }; Write-Host '[OK] Open WebUI API accepted the key.'; $env:ENGINEER_OS_OPEN_WEBUI_API_KEY=$key; Write-Host '[4/5] Running ENGINEER OS local runtime with Python 3.11...'; $uv=Get-Command uv -ErrorAction SilentlyContinue; if (-not $uv) { throw 'uv is required to run the ENGINEER OS local runtime with Python 3.11' }; & $uv.Source run --python 3.11 python scripts/local_openwebui_smoke.py; $code=$LASTEXITCODE; if ($code -ne 0) { throw ('ENGINEER OS local runtime exited with code ' + $code) }; Write-Host ''; Write-Host '[5/5] RESULT'; Write-Host '=========================================='; Write-Host 'Open WebUI API: PASSED'; Write-Host ('Model: ' + $env:ENGINEER_OS_OPEN_WEBUI_MODEL); Write-Host 'ENGINEER OS runtime transport: PASSED'; Write-Host 'Engineering status: see JSON result above (UNCERTAINTY is expected for this no-materials smoke test).'; Write-Host '=========================================='; exit 0 } catch { Write-Host ('[ERROR] Open WebUI/runtime check failed: ' + $_.Exception.Message); exit 1 }"
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
pause
endlocal
