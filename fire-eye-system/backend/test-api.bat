@echo off
chcp 65001 >nul
echo ========================================
echo 🧪 测试后端API
echo ========================================
echo.

cd /d "%~dp0"

python test_api.py

echo.
pause
