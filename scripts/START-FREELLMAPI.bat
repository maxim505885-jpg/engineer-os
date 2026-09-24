@echo off
setlocal
title ENGINEER OS - Free Local Stack

cd /d "%~dp0.."

echo.
echo ==========================================
echo     ENGINEER OS - FREE LOCAL STACK
echo ==========================================
echo.

echo [1/4] Checking Docker...
where docker >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Docker Desktop is required to start FreeLLMAPI.
  echo Install Docker Desktop, then run this launcher again.
  pause
  exit /b 1
)

echo [2/4] Preparing FreeLLMAPI...
if not exist "%CD%\freellmapi" (
  echo [INFO] Cloning FreeLLMAPI into .\freellmapi ...
  git clone https://github.com/maxim505885-jpg/freellmapi.git "%CD%\freellmapi"
  if errorlevel 1 (
    echo [ERROR] Could not clone FreeLLMAPI.
    pause
    exit /b 1
  )
)

if not exist "%CD%\freellmapi\.env" (
  echo [INFO] Creating FreeLLMAPI encryption key...
  powershell -NoProfile -Command "$b=New-Object Byte[] 32; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b); $k=-join ($b | %% { \"{0:x2}\" -f $_ }); \"ENCRYPTION_KEY=$k`nPORT=3001\" | Out-File -Encoding utf8 \"%CD%\freellmapi\.env\""
  if errorlevel 1 (
    echo [ERROR] Could not create FreeLLMAPI .env.
    pause
    exit /b 1
  )
)

echo [3/4] Starting FreeLLMAPI...
docker compose -f "%CD%\freellmapi\docker-compose.yml" up -d
if errorlevel 1 (
  echo [ERROR] FreeLLMAPI failed to start.
  pause
  exit /b 1
)

echo Waiting for FreeLLMAPI...
powershell -NoProfile -Command "$ok=$false; 1..60 | %% { try { $r=Invoke-WebRequest -UseBasicParsing -Uri \"http://127.0.0.1:3001/api/ping\" -TimeoutSec 2; if ($r.StatusCode -eq 200) { $ok=$true; break } } catch {}; Start-Sleep -Seconds 2 }; if ($ok) { exit 0 } else { exit 1 }"
if errorlevel 1 (
  echo [ERROR] FreeLLMAPI did not become available on port 3001.
  echo Run: docker compose -f freellmapi\docker-compose.yml logs --tail 100 freellmapi
  pause
  exit /b 1
)

echo [4/4] FreeLLMAPI is running.
echo.
echo Open the dashboard:
echo http://127.0.0.1:3001
echo.
echo First launch:
echo 1. Create the local FreeLLMAPI account.
echo 2. Add only free provider keys you own.
echo 3. Copy the unified freellmapi-... key.
echo 4. Do NOT paste that key into GitHub or ChatGPT.
echo.
echo ENGINEER OS can then use:
echo   http://127.0.0.1:3001/v1
echo.
pause
endlocal
