@echo off
chcp 65001 >nul
echo ========================================
echo 🔥 FireEye 数据库清空工具
echo ========================================
echo.

cd /d "%~dp0"

python clear_database.py

echo.
pause
