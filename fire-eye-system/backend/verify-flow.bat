@echo off
chcp 65001 >nul
echo ========================================
echo 🧪 验证完整数据流程
echo ========================================
echo.
echo 此工具将模拟完整的文档上传流程
echo 并验证数据是否正确保存到数据库
echo.
pause

cd /d "%~dp0"

python verify_flow.py

echo.
pause
