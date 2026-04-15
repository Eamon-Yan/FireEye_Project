@echo off
setlocal

if /i not "%~1"=="--run" (
  start "FireEye Prod" cmd /k ""%~f0" --run"
  exit /b 0
)

cd /d "%~dp0"
echo [FireEye] Starting production environment...
docker compose -f docker-compose.prod.yml up -d
set "SCRIPT_EXIT=%ERRORLEVEL%"

if not "%SCRIPT_EXIT%"=="0" (
  echo [FireEye] Failed to start production environment
  goto :end
)

echo [FireEye] Production environment is up
echo Frontend: http://localhost:5000
echo Backend : http://localhost:8000

:end
echo.
pause
exit /b %SCRIPT_EXIT%
