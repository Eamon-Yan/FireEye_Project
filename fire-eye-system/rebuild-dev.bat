@echo off
setlocal

if /i not "%~1"=="--run" (
  start "FireEye Rebuild Dev" cmd /k ""%~f0" --run"
  exit /b 0
)

cd /d "%~dp0"
echo [FireEye] Rebuilding development environment...
docker compose up -d --build
set "SCRIPT_EXIT=%ERRORLEVEL%"

if not "%SCRIPT_EXIT%"=="0" (
  echo [FireEye] Failed to rebuild development environment
  goto :end
)

echo [FireEye] Development environment rebuilt successfully

:end
echo.
pause
exit /b %SCRIPT_EXIT%
