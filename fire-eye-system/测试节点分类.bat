@echo off
chcp 65001 >nul
echo ========================================
echo 🔥 FireEye 节点分类测试流程
echo ========================================
echo.
echo 此脚本将帮助你测试新的节点分类逻辑
echo.
echo 测试步骤：
echo 1. 清空数据库
echo 2. 重启后端服务（确保新代码生效）
echo 3. 提示你上传测试文档
echo 4. 提示你查看图谱验证
echo.
pause

echo.
echo ========================================
echo 步骤 1/4: 清空数据库
echo ========================================
echo.

cd backend
python clear_database.py

if errorlevel 1 (
    echo.
    echo ❌ 清空数据库失败！
    echo 请确保：
    echo 1. 后端服务正在运行
    echo 2. Neo4j数据库正在运行
    pause
    exit /b 1
)

echo.
echo ========================================
echo 步骤 2/4: 重启后端服务
echo ========================================
echo.
echo ⚠️  请手动重启后端服务以确保新代码生效：
echo.
echo 1. 找到运行后端的命令行窗口
echo 2. 按 Ctrl+C 停止服务
echo 3. 运行 start-backend.bat 重新启动
echo.
echo 完成后按任意键继续...
pause >nul

echo.
echo ========================================
echo 步骤 3/4: 上传测试文档
echo ========================================
echo.
echo 📤 请在浏览器中上传测试文档：
echo.
echo 1. 打开浏览器访问: http://localhost:8080/upload
echo 2. 上传文件: 测试文档-火灾调查报告示例.txt
echo 3. 等待处理完成（约10-30秒）
echo.
echo 完成后按任意键继续...
pause >nul

echo.
echo ========================================
echo 步骤 4/4: 查看图谱验证
echo ========================================
echo.
echo 📊 请在浏览器中查看图谱：
echo.
echo 1. 打开浏览器访问: http://localhost:8080/graph
echo 2. 检查节点颜色分布：
echo    🔴 红色 = 火灾事件 (FireEvent)
echo    🟠 橙色 = 安全隐患 (Hazard)
echo    🟣 紫色 = 后果影响 (Consequence)
echo.
echo 3. 点击不同颜色的节点查看详情
echo 4. 确认"类型"字段显示正确
echo.
echo ========================================
echo 预期结果：
echo ========================================
echo.
echo 应该看到三种颜色的节点：
echo.
echo 🔴 红色节点示例：
echo    - 电路短路
echo    - 产生电弧
echo    - 引燃包装材料
echo    - 火势蔓延
echo.
echo 🟠 橙色节点示例：
echo    - 电线绝缘层破损
echo    - 电气线路老化
echo    - 安全检查不到位
echo.
echo 🟣 紫色节点示例：
echo    - 造成财产损失
echo    - 人员伤亡
echo    - 设备损坏
echo.
echo ========================================
echo 测试完成！
echo ========================================
echo.
echo 如果节点颜色仍然全是红色，请检查：
echo 1. 后端服务是否已重启
echo 2. 浏览器是否已清除缓存（Ctrl+Shift+Delete）
echo 3. 后端代码是否正确保存
echo.
pause
