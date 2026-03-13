#!/usr/bin/env python3
"""
创建最小化测试端点
"""

from fastapi import FastAPI, Depends
from typing import Optional
import uvicorn

app = FastAPI()

# 模拟依赖
async def get_test_service():
    return "test_service"

@app.get("/test1")
async def test1():
    """最简单的端点"""
    return {"status": "success", "message": "test1"}

@app.get("/test2")
async def test2(service: str = Depends(get_test_service)):
    """带依赖的端点"""
    return {"status": "success", "message": "test2", "service": service}

@app.get("/test3")
async def test3(
    limit: int = 100,
    include_relationships: bool = True
):
    """带参数的端点"""
    return {
        "status": "success",
        "message": "test3",
        "limit": limit,
        "include_relationships": include_relationships
    }

@app.get("/test4")
async def test4(
    node_types: Optional[str] = None,
    search_text: Optional[str] = None,
    limit: int = 100,
    include_relationships: bool = True,
    service: str = Depends(get_test_service)
):
    """完整参数的端点"""
    return {
        "status": "success",
        "message": "test4",
        "node_types": node_types,
        "search_text": search_text,
        "limit": limit,
        "include_relationships": include_relationships,
        "service": service
    }

if __name__ == "__main__":
    print("启动测试服务器在 http://localhost:8001")
    print("测试端点:")
    print("  http://localhost:8001/test1")
    print("  http://localhost:8001/test2")
    print("  http://localhost:8001/test3")
    print("  http://localhost:8001/test4")
    uvicorn.run(app, host="0.0.0.0", port=8001)
