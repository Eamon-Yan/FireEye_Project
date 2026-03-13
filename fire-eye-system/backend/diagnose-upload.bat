@echo off
chcp 65001 >nul
echo ========================================
echo 🔍 FireEye 数据库诊断工具
echo ========================================
echo.

cd /d "%~dp0"

python diagnose_upload.py

echo.
pause
