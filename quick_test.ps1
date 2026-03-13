# Quick Test Script for Fire-Eye System
# Date: 2026-02-18

Write-Host "=========================================="
Write-Host "Fire-Eye System Quick Test"
Write-Host "=========================================="
Write-Host ""

# Test 1: Health Check
Write-Host "Test 1: Backend Health Check"
docker exec astrbot curl -s http://fire-eye-backend:8000/health
Write-Host ""
Write-Host ""

# Test 2: Stats API
Write-Host "Test 2: Stats API"
docker exec astrbot curl -s http://fire-eye-backend:8000/api/v1/chat/stats -H "X-API-Key: smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA"
Write-Host ""
Write-Host ""

# Test 3: Query API
Write-Host "Test 3: Query API"
docker exec astrbot curl -s -X POST http://fire-eye-backend:8000/api/v1/chat/query -H "X-API-Key: smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA" -H "Content-Type: application/json" -d '{\"query\": \"fire\"}'
Write-Host ""
Write-Host ""

# Test 4: Plugin Status
Write-Host "Test 4: Plugin Load Status"
docker logs astrbot 2>&1 | Select-String -Pattern "Fire-Eye"
Write-Host ""
Write-Host ""

# Test 5: Telegram Status
Write-Host "Test 5: Telegram Bot Status"
docker logs astrbot 2>&1 | Select-String -Pattern "Telegram" | Select-Object -Last 3
Write-Host ""
Write-Host ""

# Test 6: Redis Status
Write-Host "Test 6: Redis Status"
docker exec fire-eye-redis redis-cli ping
Write-Host ""
Write-Host ""

Write-Host "=========================================="
Write-Host "Test Complete"
Write-Host "=========================================="
