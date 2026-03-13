"""
测试文件上传 API
模拟插件的文件上传流程
"""

import requests
import time
import os

# 配置
API_URL = "http://localhost:8000/api/v1"
API_KEY = "smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA"

headers = {
    "X-API-Key": API_KEY
}

def test_upload_api():
    """测试文件上传 API"""
    print("=" * 60)
    print("测试文件上传 API")
    print("=" * 60)
    
    # 1. 检查后端健康状态
    print("\n1. 检查后端健康状态...")
    try:
        response = requests.get(f"{API_URL}/chat/stats", headers=headers, timeout=5)
        if response.status_code == 200:
            print("✅ 后端正常运行")
            data = response.json().get("data", {})
            print(f"   当前事件数: {data.get('total_events', 0)}")
            print(f"   当前实体数: {data.get('total_entities', 0)}")
        else:
            print(f"❌ 后端响应异常: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 无法连接到后端: {e}")
        return
    
    # 2. 准备测试文件
    print("\n2. 准备测试文件...")
    test_file_path = "fire-eye-system/测试文档-火灾调查报告示例.txt"
    
    if not os.path.exists(test_file_path):
        print(f"❌ 测试文件不存在: {test_file_path}")
        return
    
    print(f"✅ 找到测试文件: {test_file_path}")
    file_size = os.path.getsize(test_file_path)
    print(f"   文件大小: {file_size} 字节 ({file_size/1024:.2f} KB)")
    
    # 3. 上传文件
    print("\n3. 上传文件到后端...")
    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': (os.path.basename(test_file_path), f, 'text/plain')}
            data = {'session_id': 'test_session_123'}
            
            response = requests.post(
                f"{API_URL}/chat/upload",
                headers={"X-API-Key": API_KEY},
                files=files,
                data=data,
                timeout=60
            )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 文件上传成功")
            
            task_data = result.get("data", {})
            task_id = task_data.get("task_id")
            document_id = task_data.get("document_id")
            
            print(f"   任务ID: {task_id}")
            print(f"   文档ID: {document_id}")
            print(f"   状态: {task_data.get('status')}")
            
            # 4. 轮询任务状态
            if task_id:
                print("\n4. 轮询任务状态...")
                poll_task_status(task_id)
            else:
                print("❌ 未获得任务ID")
        else:
            print(f"❌ 上传失败: {response.status_code}")
            print(f"   响应: {response.text}")
    
    except Exception as e:
        print(f"❌ 上传过程出错: {e}")

def poll_task_status(task_id, max_attempts=60, interval=3):
    """轮询任务状态"""
    print(f"   开始轮询任务 {task_id}...")
    print(f"   最大尝试次数: {max_attempts}, 间隔: {interval}秒")
    
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(
                f"{API_URL}/chat/status/{task_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                task_data = result.get("data", {})
                status = task_data.get("status")
                progress = task_data.get("progress", 0)
                
                print(f"   [{attempt}/{max_attempts}] 状态: {status}, 进度: {progress}%")
                
                if status == "completed":
                    print("\n✅ 任务完成！")
                    display_result(task_data.get("result", {}))
                    return True
                
                elif status == "failed":
                    print(f"\n❌ 任务失败")
                    print(f"   错误: {task_data.get('error', '未知错误')}")
                    return False
                
                elif status in ["pending", "processing"]:
                    if attempt < max_attempts:
                        time.sleep(interval)
                    continue
                
                else:
                    print(f"\n⚠️  未知状态: {status}")
                    return False
            
            else:
                print(f"   ❌ 查询失败: {response.status_code}")
                return False
        
        except Exception as e:
            print(f"   ❌ 轮询出错: {e}")
            if attempt < max_attempts:
                time.sleep(interval)
            continue
    
    print(f"\n⏱️  任务超时（{max_attempts * interval}秒）")
    return False

def display_result(result):
    """显示分析结果"""
    print("\n" + "=" * 60)
    print("分析结果")
    print("=" * 60)
    
    event_chains = result.get("event_chains", [])
    node_count = result.get("node_count", 0)
    relationship_count = result.get("relationship_count", 0)
    
    print(f"\n📊 统计信息:")
    print(f"   节点数量: {node_count}")
    print(f"   关系数量: {relationship_count}")
    print(f"   事件链数量: {len(event_chains)}")
    
    if event_chains:
        print(f"\n🔗 提取的事件链（前5条）:")
        for i, chain in enumerate(event_chains[:5], 1):
            source = chain.get("source", "")
            relation = chain.get("relation", "")
            target = chain.get("target", "")
            confidence = chain.get("confidence", 0)
            
            print(f"\n   {i}. {source} → {relation} → {target}")
            print(f"      置信度: {confidence:.2f}")
        
        if len(event_chains) > 5:
            print(f"\n   ... 还有 {len(event_chains) - 5} 条事件链")
    
    print("\n" + "=" * 60)

def test_query_after_upload():
    """测试上传后的查询功能"""
    print("\n" + "=" * 60)
    print("测试查询功能")
    print("=" * 60)
    
    # 查询刚刚上传的内容
    test_queries = ["火", "电", "短路"]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        try:
            response = requests.post(
                f"{API_URL}/chat/query",
                headers=headers,
                json={"query": query, "session_id": "test_session_123"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    data = result.get("data", {})
                    results = data.get("results", [])
                    print(f"✅ 找到 {len(results)} 条结果")
                    
                    for i, item in enumerate(results[:3], 1):
                        node_type = item.get("type", "Unknown")
                        name = item.get("name", item.get("id", ""))
                        print(f"   {i}. [{node_type}] {name}")
                else:
                    print(f"❌ 查询失败: {result.get('detail')}")
            else:
                print(f"❌ 请求失败: {response.status_code}")
        
        except Exception as e:
            print(f"❌ 查询出错: {e}")

if __name__ == "__main__":
    print("\n🔥 火瞳系统 - 文件上传 API 测试")
    print("=" * 60)
    
    # 测试上传
    test_upload_api()
    
    # 等待一下，让数据完全写入
    print("\n等待5秒...")
    time.sleep(5)
    
    # 测试查询
    test_query_after_upload()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
