@echo off
setlocal

if /i not "%~1"=="--run" (
  start "FireEye Dev" cmd /k ""%~f0" --run"
  exit /b 0
)

cd /d "%~dp0"
echo [FireEye] Starting development environment...
docker compose up -d
set "SCRIPT_EXIT=%ERRORLEVEL%"

if not "%SCRIPT_EXIT%"=="0" (
  echo [FireEye] Failed to start development environment
  goto :end
)

echo [FireEye] Development environment is up
echo Frontend: http://localhost:5000
echo Backend : http://localhost:8000

:end
echo.
pause
exit /b %SCRIPT_EXIT%
