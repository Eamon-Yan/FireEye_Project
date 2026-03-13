@echo off
echo Starting FireEye Frontend...
echo.
cd /d "%~dp0"
npx next dev -H localhost -p 8080
pause
