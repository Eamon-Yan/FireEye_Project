"""
API集成测试示例
演示完整的API工作流程
"""

import asyncio
import httpx
import json
from pathlib import Path
import tempfile
import os

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"


async def test_api_workflow():
    """测试完整的API工作流程"""
    print("🚀 开始API集成测试...")
    
    async with httpx.AsyncClient() as client:
        
        # 1. 健康检查
        print("\n1️⃣ 健康检查...")
        try:
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"   ✅ 服务状态: {health_data['status']}")
                print(f"   📊 Neo4j: {health_data['database']['neo4j']}")
                print(f"   📊 Redis: {health_data['database']['redis']}")
            else:
                print(f"   ❌ 健康检查失败: {response.status_code}")
                return
        except Exception as e:
            print(f"   ❌ 连接失败: {e}")
            return
        
        # 2. 检查支持的文件格式
        print("\n2️⃣ 检查支持的文件格式...")
        try:
            response = await client.get(f"{BASE_URL}/documents/supported-formats")
            if response.status_code == 200:
                formats_data = response.json()
                print(f"   ✅ 支持格式: {formats_data['data']['supported_formats']}")
                print(f"   📏 最大文件大小: {formats_data['data']['max_file_size_mb']} MB")
            else:
                print(f"   ❌ 获取格式信息失败: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 请求失败: {e}")
        
        # 3. 创建测试文档
        print("\n3️⃣ 创建测试文档...")
        test_content = """
        火灾事故调查报告
        
        事故经过：
        2023年10月15日下午16:30，某住宅小区地下车库发生火灾。
        当时有居民发现电瓶车充电区域冒出浓烟，随即听到爆炸声。
        起火的是一辆正在充电的电动自行车，火势迅速蔓延至附近停放的其他电动车。
        现场堆放的纸箱、塑料制品等可燃物助长了火势。
        小区保安立即报警并组织人员疏散，消防队于17:00到达现场。
        经过1小时的扑救，火势完全扑灭，但已造成5辆电动自行车烧毁。
        
        原因分析：
        经过专业机构调查，确定事故原因如下：
        主要原因：电动自行车充电器长期使用导致老化，内部电路电气短路产生高温，
        引燃了充电器外壳的可燃材料，进而点燃蓄电池组。
        次要原因：地下车库通风不良，可燃气体积聚；
        车库内违规堆放大量纸张、橡胶等易燃物品。
        管理原因：物业管理不善，缺乏定期的安全检查，
        未及时发现和更换老化的充电设备。
        """
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(test_content)
            temp_file_path = f.name
        
        print(f"   ✅ 测试文档已创建: {temp_file_path}")
        
        # 4. 测试统一处理端点
        print("\n4️⃣ 测试统一文档处理...")
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('test_document.txt', f, 'text/plain')}
                data = {
                    'apply_validation': 'true',
                    'save_to_graph': 'true'
                }
                
                # 增加超时时间以处理LLM请求
                timeout = httpx.Timeout(60.0)  # 60秒超时
                async with httpx.AsyncClient(timeout=timeout) as long_client:
                    response = await long_client.post(
                        f"{BASE_URL}/documents/process",
                        files=files,
                        data=data
                    )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 处理成功: {result['message']}")
                
                # 显示处理结果
                data = result['data']
                print(f"   📄 文档ID: {data['document_id']}")
                print(f"   📊 章节数量: {data['document_sections']['section_count']}")
                print(f"   🔗 事件链数量: {data['event_chains']['count']}")
                
                # 显示处理统计
                stats = data['processing_statistics']
                print(f"   📈 原始事件链: {stats['raw_chains']}")
                print(f"   ✅ 有效事件链: {stats['valid_chains']}")
                print(f"   ❌ 过滤事件链: {stats['filtered_chains']}")
                print(f"   📊 验证通过率: {stats['validation_rate']:.2%}")
                print(f"   🎯 平均置信度: {stats['avg_confidence']:.2f}")
                
                # 显示图存储结果
                graph_storage = data['graph_storage']
                print(f"   💾 图存储: {'启用' if graph_storage['enabled'] else '禁用'}")
                print(f"   💾 保存数量: {graph_storage['saved_count']}")
                
                # 显示部分事件链
                print("\n   🔗 提取的事件链示例:")
                for i, chain in enumerate(data['event_chains']['chains'][:3], 1):
                    print(f"      {i}. {chain['source']}")
                    print(f"         → {chain['relation']} →")
                    print(f"         {chain['target']}")
                    print(f"         置信度: {chain['confidence']:.2f}")
                
                # 保存文档ID用于后续测试
                document_id = data['document_id']
                
            else:
                print(f"   ❌ 处理失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
                return
                
        except Exception as e:
            print(f"   ❌ 请求失败: {e}")
            return
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
        # 5. 测试图数据查询
        print("\n5️⃣ 测试图数据查询...")
        try:
            response = await client.get(
                f"{BASE_URL}/graph/query",
                params={
                    'limit': 10,
                    'include_relationships': True
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 查询成功: {result['message']}")
                
                data = result['data']
                print(f"   📊 节点数量: {len(data['nodes'])}")
                print(f"   🔗 关系数量: {len(data['relationships'])}")
                
                # 显示统计信息
                if 'statistics' in data and data['statistics']:
                    stats = data['statistics']
                    print(f"   📈 总节点数: {stats.get('total_nodes', 'N/A')}")
                    print(f"   📈 总关系数: {stats.get('total_relationships', 'N/A')}")
                
                # 显示部分节点
                if data['nodes']:
                    print("\n   📊 图中的节点示例:")
                    for i, node in enumerate(data['nodes'][:3], 1):
                        print(f"      {i}. [{node['type']}] {node.get('description', node['id'])}")
                
            else:
                print(f"   ❌ 查询失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
                
        except Exception as e:
            print(f"   ❌ 请求失败: {e}")
        
        # 6. 测试图统计信息
        print("\n6️⃣ 测试图统计信息...")
        try:
            response = await client.get(f"{BASE_URL}/graph/statistics")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 获取统计成功")
                
                stats = result['data']
                print(f"   📊 总节点数: {stats.get('total_nodes', 0)}")
                print(f"   🔗 总关系数: {stats.get('total_relationships', 0)}")
                
                if 'node_type_counts' in stats:
                    print("   📈 节点类型分布:")
                    for node_type, count in stats['node_type_counts'].items():
                        print(f"      - {node_type}: {count}")
                
            else:
                print(f"   ❌ 获取统计失败: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 请求失败: {e}")
        
        # 7. 测试搜索功能
        print("\n7️⃣ 测试节点搜索...")
        try:
            response = await client.get(
                f"{BASE_URL}/graph/search/nodes",
                params={
                    'q': '电动自行车',
                    'limit': 5
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 搜索成功: {result['message']}")
                
                nodes = result['data']['nodes']
                if nodes:
                    print("   🔍 搜索结果:")
                    for i, node in enumerate(nodes, 1):
                        desc = node.get('properties', {}).get('description', node.get('id', 'N/A'))
                        print(f"      {i}. {desc}")
                else:
                    print("   📭 未找到匹配的节点")
                
            else:
                print(f"   ❌ 搜索失败: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 请求失败: {e}")


async def test_simple_upload():
    """测试简单文档上传"""
    print("\n🔄 测试简单文档上传...")
    
    async with httpx.AsyncClient() as client:
        # 创建简单测试文档
        test_content = """
        事故经过：电瓶车充电时发生短路起火。
        原因分析：充电器老化导致电气故障。
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(test_content)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('simple_test.txt', f, 'text/plain')}
                
                response = await client.post(
                    f"{BASE_URL}/documents/upload",
                    files=files
                )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 上传成功: {result['message']}")
                
                data = result['data']
                print(f"   📄 文档ID: {data['document_id']}")
                print(f"   📊 章节: {list(data['sections'].keys())}")
                
            else:
                print(f"   ❌ 上传失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
                
        except Exception as e:
            print(f"   ❌ 请求失败: {e}")
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)


async def main():
    """主函数"""
    print("🔥 火瞳系统 - API集成测试")
    print("=" * 60)
    print("⚠️  请确保后端服务已启动 (python -m uvicorn app.main:app --reload)")
    print()
    
    # 运行测试
    await test_api_workflow()
    await test_simple_upload()
    
    print("\n" + "=" * 60)
    print("✅ API集成测试完成!")
    print("\n💡 提示:")
    print("   - 可以访问 http://localhost:8000/docs 查看API文档")
    print("   - 使用 POST /api/v1/documents/process 进行完整文档处理")
    print("   - 使用 GET /api/v1/graph/query 查询图数据")


if __name__ == "__main__":
    asyncio.run(main())