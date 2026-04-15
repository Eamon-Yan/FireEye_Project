@echo off
setlocal

if /i not "%~1"=="--run" (
  start "FireEye Rebuild Prod" cmd /k ""%~f0" --run"
  exit /b 0
)

cd /d "%~dp0"
echo [FireEye] Rebuilding production environment...
docker compose -f docker-compose.prod.yml up -d --build
set "SCRIPT_EXIT=%ERRORLEVEL%"

if not "%SCRIPT_EXIT%"=="0" (
  echo [FireEye] Failed to rebuild production environment
  goto :end
)

echo [FireEye] Production environment rebuilt successfully

:end
echo.
pause
exit /b %SCRIPT_EXIT%
