@echo off
echo ============================================================
echo 清理Python缓存并验证代码
echo ============================================================
echo.

echo 1. 清理__pycache__目录...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
echo    完成
echo.

echo 2. 删除.pyc文件...
del /s /q *.pyc 2>nul
echo    完成
echo.

echo 3. 验证graph.py语法...
python -m py_compile app\api\v1\endpoints\graph.py
if %ERRORLEVEL% EQU 0 (
    echo    [32m✓ 语法正确[0m
) else (
    echo    [31m✗ 语法错误[0m
    pause
    exit /b 1
)
echo.

echo 4. 检查路由定义...
python check_startup_error.py
echo.

echo ============================================================
echo 清理完成！现在请重启后端服务
echo ============================================================
echo.
echo 步骤:
echo 1. 在运行后端的窗口按 Ctrl+C
echo 2. 运行: start-backend.bat
echo 3. 等待启动完成
echo 4. 运行: test-api.bat
echo.
pause
