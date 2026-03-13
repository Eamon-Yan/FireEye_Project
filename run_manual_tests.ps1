# 火瞳系统手动测试脚本
# 创建日期: 2026-02-18

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "火瞳系统手动测试" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 测试计数器
$passed = 0
$failed = 0
$total = 0

# 测试 1.1: 健康检查
Write-Host "测试 1.1: 健康检查" -ForegroundColor Yellow
$total++
try {
    $result = docker exec astrbot curl -s http://fire-eye-backend:8000/health 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 通过" -ForegroundColor Green
        Write-Host $result
        $passed++
    } else {
        Write-Host "❌ 失败" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "❌ 失败: $_" -ForegroundColor Red
    $failed++
}
Write-Host ""

# 测试 1.2: 统计接口
Write-Host "测试 1.2: 统计接口" -ForegroundColor Yellow
$total++
try {
    $result = docker exec astrbot curl -s http://fire-eye-backend:8000/api/v1/chat/stats -H "X-API-Key: smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA" 2>&1
    if ($LASTEXITCODE -eq 0 -and $result -match "success") {
        Write-Host "✅ 通过" -ForegroundColor Green
        Write-Host $result
        $passed++
    } else {
        Write-Host "❌ 失败" -ForegroundColor Red
        Write-Host $result
        $failed++
    }
} catch {
    Write-Host "❌ 失败: $_" -ForegroundColor Red
    $failed++
}
Write-Host ""

# 测试 1.3: 查询接口
Write-Host "测试 1.3: 查询接口" -ForegroundColor Yellow
$total++
try {
    $result = docker exec astrbot curl -s -X POST http://fire-eye-backend:8000/api/v1/chat/query -H "X-API-Key: smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA" -H "Content-Type: application/json" -d '{\"query\": \"火灾\"}' 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 通过" -ForegroundColor Green
        Write-Host $result
        $passed++
    } else {
        Write-Host "❌ 失败" -ForegroundColor Red
        Write-Host $result
        $failed++
    }
} catch {
    Write-Host "❌ 失败: $_" -ForegroundColor Red
    $failed++
}
Write-Host ""

# 测试 1.4: 认证失败测试
Write-Host "测试 1.4: 认证失败测试 (应该返回 401)" -ForegroundColor Yellow
$total++
try {
    $result = docker exec astrbot curl -s -w "\n%{http_code}" http://fire-eye-backend:8000/api/v1/chat/stats -H "X-API-Key: wrong-key" 2>&1
    if ($result -match "401" -or $result -match "Invalid") {
        Write-Host "✅ 通过 (正确拒绝了错误的密钥)" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "❌ 失败 (应该拒绝错误的密钥)" -ForegroundColor Red
        Write-Host $result
        $failed++
    }
} catch {
    Write-Host "❌ 失败: $_" -ForegroundColor Red
    $failed++
}
Write-Host ""

# 测试 2.1: 插件加载状态
Write-Host "测试 2.1: 插件加载状态" -ForegroundColor Yellow
$total++
try {
    $result = docker logs astrbot 2>&1 | Select-String -Pattern "Fire-Eye.*initialized"
    if ($result) {
        Write-Host "✅ 通过 - 插件已加载" -ForegroundColor Green
        Write-Host $result
        $passed++
    } else {
        Write-Host "❌ 失败 - 未找到插件加载日志" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "❌ 失败: $_" -ForegroundColor Red
    $failed++
}
Write-Host ""

# 测试 2.2: 检查插件文件
Write-Host "测试 2.2: 检查插件文件完整性" -ForegroundColor Yellow
$total++
try {
    $result = docker exec astrbot ls /AstrBot/data/plugins/astrbot-plugin-fireeye/main.py 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 通过 - 插件文件存在" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "❌ 失败 - 插件文件不存在" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "❌ 失败: $_" -ForegroundColor Red
    $failed++
}
Write-Host ""

# 测试 3.1: Telegram 状态
Write-Host "测试 3.1: Telegram Bot 状态" -ForegroundColor Yellow
$total++
try {
    $result = docker logs astrbot 2>&1 | Select-String -Pattern "Telegram.*running" | Select-Object -Last 1
    if ($result) {
        Write-Host "✅ 通过 - Telegram Bot 正在运行" -ForegroundColor Green
        Write-Host $result
        $passed++
    } else {
        Write-Host "⚠️  警告 - 未找到 Telegram 运行日志" -ForegroundColor Yellow
        $failed++
    }
} catch {
    Write-Host "❌ 失败: $_" -ForegroundColor Red
    $failed++
}
Write-Host ""

# 测试 4.1: 网络连通性
Write-Host "测试 4.1: 网络连通性 (AstrBot -> Backend)" -ForegroundColor Yellow
$total++
try {
    $result = docker exec astrbot ping -c 2 fire-eye-backend 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 通过 - 网络连接正常" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "❌ 失败 - 网络连接失败" -ForegroundColor Red
        Write-Host $result
        $failed++
    }
} catch {
    Write-Host "❌ 失败: $_" -ForegroundColor Red
    $failed++
}
Write-Host ""

# 测试 5.1: Redis 状态
Write-Host "测试 5.1: Redis 状态" -ForegroundColor Yellow
$total++
try {
    $result = docker exec fire-eye-redis redis-cli ping 2>&1
    if ($result -match "PONG") {
        Write-Host "✅ 通过 - Redis 正常运行" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "❌ 失败 - Redis 未响应" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "❌ 失败: $_" -ForegroundColor Red
    $failed++
}
Write-Host ""

# 测试 5.2: Neo4j 状态
Write-Host "测试 5.2: Neo4j 状态" -ForegroundColor Yellow
$total++
try {
    $result = docker exec fire-eye-neo4j cypher-shell -u neo4j -p password "RETURN 1" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 通过 - Neo4j 正常运行" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "❌ 失败 - Neo4j 连接失败" -ForegroundColor Red
        Write-Host $result
        $failed++
    }
} catch {
    Write-Host "❌ 失败: $_" -ForegroundColor Red
    $failed++
}
Write-Host ""

# 测试总结
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "测试总结" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "总测试数: $total" -ForegroundColor White
Write-Host "通过: $passed" -ForegroundColor Green
Write-Host "失败: $failed" -ForegroundColor Red
Write-Host "成功率: $([math]::Round($passed/$total*100, 2))%" -ForegroundColor $(if ($passed -eq $total) { "Green" } elseif ($passed -ge $total * 0.7) { "Yellow" } else { "Red" })
Write-Host ""

if ($passed -eq $total) {
    Write-Host "🎉 所有测试通过！系统运行正常。" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步: 实现插件的命令处理器功能" -ForegroundColor Cyan
    Write-Host "  1. 实现 /火瞳查询 命令" -ForegroundColor White
    Write-Host "  2. 实现 /火瞳统计 命令" -ForegroundColor White
    Write-Host "  3. 实现 /火瞳帮助 命令" -ForegroundColor White
    Write-Host "  4. 实现 /火瞳上传 命令" -ForegroundColor White
} elseif ($passed -ge $total * 0.7) {
    Write-Host "⚠️  大部分测试通过，但有一些问题需要解决。" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "建议: 查看失败的测试项，修复问题后再继续。" -ForegroundColor Yellow
} else {
    Write-Host "❌ 多个测试失败，需要排查问题。" -ForegroundColor Red
    Write-Host ""
    Write-Host "建议操作:" -ForegroundColor Yellow
    Write-Host "  1. 检查所有容器是否正常运行: docker ps" -ForegroundColor White
    Write-Host "  2. 查看后端日志: docker logs fire-eye-backend" -ForegroundColor White
    Write-Host "  3. 查看 AstrBot 日志: docker logs astrbot" -ForegroundColor White
    Write-Host "  4. 检查网络配置: docker network ls" -ForegroundColor White
}

Write-Host ""
Write-Host "详细测试指南: MANUAL_TEST_GUIDE.md" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
