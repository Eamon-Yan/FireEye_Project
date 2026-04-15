@echo off
setlocal EnableExtensions EnableDelayedExpansion

if /i not "%~1"=="--run" (
  start "FireEye Env Check" cmd /k ""%~f0" --run"
  exit /b 0
)

cd /d "%~dp0"

set "EXIT_CODE=0"

echo [FireEye] Running environment checks...
echo.

echo [1/5] Checking Docker Desktop / Docker Engine
docker info >nul 2>nul
if errorlevel 1 (
  echo [FAIL] Docker is not available. Start Docker Desktop first.
  set "EXIT_CODE=1"
) else (
  echo [PASS] Docker is available.
)
echo.

echo [2/5] Checking OPENAI_API_KEY
set "API_KEY_FOUND="
if defined OPENAI_API_KEY set "API_KEY_FOUND=1"

if not defined API_KEY_FOUND (
  if exist ".env" (
    findstr /b /c:"OPENAI_API_KEY=" ".env" >nul 2>nul && set "API_KEY_FOUND=1"
  )
)

if not defined API_KEY_FOUND (
  if exist "backend\.env" (
    findstr /b /c:"OPENAI_API_KEY=" "backend\.env" >nul 2>nul && set "API_KEY_FOUND=1"
  )
)

if defined API_KEY_FOUND (
  echo [PASS] OPENAI_API_KEY was found.
) else (
  echo [WARN] OPENAI_API_KEY was not found. LLM features may fail.
)
echo.

echo [3/5] Checking important ports
call :check_port 5000 frontend
call :check_port 8000 backend
call :check_port 7474 neo4j-http
call :check_port 7687 neo4j-bolt
call :check_port 6125 astrbot
echo.

echo [4/5] Checking container runtime status
call :check_container fire-eye-backend
call :check_container fire-eye-frontend
call :check_container fire-eye-neo4j
call :check_container fire-eye-redis
echo.

echo [5/5] Checking container health status
call :check_health fire-eye-backend
call :check_health fire-eye-frontend
call :check_health fire-eye-neo4j
call :check_health fire-eye-redis
echo.

if "%EXIT_CODE%"=="0" (
  echo [FireEye] Environment check finished. No blocking issue found.
) else (
  echo [FireEye] Environment check finished. Issues need attention.
)

echo.
pause
exit /b %EXIT_CODE%

:check_port
set "PORT=%~1"
set "LABEL=%~2"
netstat -ano | findstr /r /c:":%PORT% .*LISTENING" >nul 2>nul
if errorlevel 1 (
  echo [INFO] Port %PORT% [%LABEL%] is not listening.
) else (
  echo [PASS] Port %PORT% [%LABEL%] is listening.
)
goto :eof

:check_container
set "CONTAINER=%~1"
set "STATE="
for /f "usebackq delims=" %%i in (`docker inspect -f "{{.State.Status}}" %CONTAINER% 2^>nul`) do set "STATE=%%i"

if not defined STATE (
  echo [WARN] Container %CONTAINER% does not exist yet.
  set "EXIT_CODE=1"
  goto :eof
)

if /i "%STATE%"=="running" (
  echo [PASS] Container %CONTAINER% is running.
) else (
  echo [FAIL] Container %CONTAINER% state: %STATE%
  set "EXIT_CODE=1"
)
goto :eof

:check_health
set "CONTAINER=%~1"
set "HEALTH="
for /f "usebackq delims=" %%i in (`docker inspect -f "{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}" %CONTAINER% 2^>nul`) do set "HEALTH=%%i"

if not defined HEALTH (
  echo [WARN] Could not read health for %CONTAINER%.
  set "EXIT_CODE=1"
  goto :eof
)

if /i "%HEALTH%"=="healthy" (
  echo [PASS] Container %CONTAINER% health is healthy.
) else if /i "%HEALTH%"=="no-healthcheck" (
  echo [INFO] Container %CONTAINER% has no healthcheck.
) else (
  echo [FAIL] Container %CONTAINER% health: %HEALTH%
  set "EXIT_CODE=1"
)
goto :eof
