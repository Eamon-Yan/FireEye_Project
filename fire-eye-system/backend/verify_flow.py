#!/usr/bin/env python3
"""
验证完整的数据流程
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db.neo4j_manager import neo4j_manager
from app.services.extraction_service import extraction_service
from app.services.graph_service import graph_service
from fastapi import UploadFile
from io import BytesIO


async def verify_complete_flow():
    """验证完整流程"""
    print("=" * 60)
    print("🧪 验证完整数据流程")
    print("=" * 60)
    print()
    
    try:
        # 读取测试文档
        test_file_path = Path(__file__).parent.parent / "测试文档-火灾调查报告示例.txt"
        
        if not test_file_path.exists():
            print(f"❌ 测试文档不存在: {test_file_path}")
            return
        
        print(f"📄 读取测试文档: {test_file_path.name}")
        
        with open(test_file_path, 'rb') as f:
            file_content = f.read()
        
        # 创建 UploadFile 对象
        upload_file = UploadFile(
            filename=test_file_path.name,
            file=BytesIO(file_content)
        )
        
        print("✅ 测试文档读取成功")
        print()
        
        # 步骤1: 处理文档
        print("📝 步骤 1: 处理文档并提取事件链...")
        document_id, document_sections, event_chains, processing_stats, layered_result = await extraction_service.process_document_with_extraction(
            upload_file,
            apply_validation=True
        )
        
        print(f"✅ 文档处理完成")
        print(f"   文档ID: {document_id}")
        print(f"   章节数: {len(document_sections.sections)}")
        print(f"   事件链数: {len(event_chains)}")
        print(f"   分层节点数: {len(layered_result.nodes) if layered_result else 0}")
        print(f"   分层边数: {len(layered_result.edges) if layered_result else 0}")
        print(f"   验证通过率: {processing_stats.get('validation_rate', 0)*100:.1f}%")
        print()
        
        # 步骤2: 保存到图数据库
        print("💾 步骤 2: 保存到图数据库...")
        await graph_service.initialize()
        
        graph_results = await graph_service.batch_create_event_chains(event_chains)
        
        print(f"✅ 保存完成: {len(graph_results)}/{len(event_chains)} 个事件链")
        print()
        
        # 步骤3: 验证数据库
        print("🔍 步骤 3: 验证数据库...")
        stats = await neo4j_manager.get_graph_statistics()
        
        print(f"   节点总数: {stats.node_count}")
        print(f"   关系总数: {stats.relationship_count}")
        print()
        
        if stats.node_type_distribution:
            print("   节点类型分布:")
            for node_type, count in stats.node_type_distribution.items():
                print(f"      {node_type}: {count}")
        print()
        
        # 步骤4: 测试查询API
        print("🔎 步骤 4: 测试图谱查询...")
        query = """
        MATCH (n)
        OPTIONAL MATCH (n)-[r]->(m)
        RETURN n, r, m
        LIMIT 10
        """
        
        results = await neo4j_manager.execute_query(query)
        print(f"✅ 查询成功: 返回 {len(results)} 条记录")
        print()
        
        # 总结
        print("=" * 60)
        print("📊 验证结果:")
        print("=" * 60)
        
        if stats.node_count > 0:
            print("✅ 数据流程正常！")
            print()
            print(f"   文档已成功处理并保存到数据库")
            print(f"   节点数: {stats.node_count}")
            print(f"   关系数: {stats.relationship_count}")
            print()
            print("💡 如果前端仍然显示空白，请:")
            print("   1. 清除浏览器缓存（Ctrl+Shift+Delete）")
            print("   2. 使用无痕模式访问")
            print("   3. 检查浏览器控制台是否有错误")
            print("   4. 访问 http://localhost:8000/api/v1/graph/query?limit=100")
        else:
            print("❌ 数据没有保存到数据库")
            print()
            print("请检查:")
            print("   1. Neo4j 是否正在运行")
            print("   2. 后端日志是否有错误")
            print("   3. 数据库连接配置是否正确")
        
        print()
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await neo4j_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(verify_complete_flow())
