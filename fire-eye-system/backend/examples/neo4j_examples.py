"""
Neo4j 管理器使用示例
"""

import asyncio
from datetime import datetime

from app.db.neo4j_manager import neo4j_manager
from app.services.graph_service import graph_service
from app.schemas import (
    FireEventNode,
    EventType,
    HazardNode,
    RiskLevel,
    ConsequenceNode,
    ImpactLevel,
    EventChainCreate,
    RelationType,
    NodeCreate,
    RelationshipCreate,
)


async def basic_connection_example():
    """基础连接示例"""
    print("=== Neo4j 连接示例 ===")
    
    try:
        # 连接数据库
        await neo4j_manager.connect()
        print("✓ 数据库连接成功")
        
        # 测试连接
        is_connected = await neo4j_manager.ping()
        print(f"✓ 连接测试: {'成功' if is_connected else '失败'}")
        
        # 获取统计信息
        stats = await neo4j_manager.get_graph_statistics()
        print(f"✓ 节点总数: {stats.node_count}")
        print(f"✓ 关系总数: {stats.relationship_count}")
        
    except Exception as e:
        print(f"✗ 连接失败: {e}")
    finally:
        await neo4j_manager.disconnect()
        print("✓ 数据库连接已关闭")
    
    print()


async def create_nodes_example():
    """创建节点示例"""
    print("=== 创建节点示例 ===")
    
    try:
        await graph_service.initialize()
        
        # 创建火灾事件节点
        fire_event = FireEventNode(
            id="example_event_001",
            event_type=EventType.CAUSE,
            description="电气线路老化导致绝缘层破损",
            standard_term="电气线路老化",
            category="电气火灾",
            severity_level=6,
            frequency=12
        )
        
        event_id = await graph_service.create_fire_event(fire_event)
        print(f"✓ 创建火灾事件节点: {event_id}")
        
        # 创建隐患节点
        hazard = HazardNode(
            id="example_hazard_001",
            description="老旧建筑电气线路存在安全隐患",
            risk_level=RiskLevel.HIGH,
            location="居民区老旧小区"
        )
        
        hazard_id = await graph_service.create_hazard(hazard)
        print(f"✓ 创建隐患节点: {hazard_id}")
        
        # 创建后果节点
        consequence = ConsequenceNode(
            id="example_consequence_001",
            description="可能造成人员伤亡和财产损失",
            impact_level=ImpactLevel.SEVERE,
            affected_area="整栋建筑"
        )
        
        consequence_id = await graph_service.create_consequence(consequence)
        print(f"✓ 创建后果节点: {consequence_id}")
        
        return event_id, hazard_id, consequence_id
        
    except Exception as e:
        print(f"✗ 创建节点失败: {e}")
        return None, None, None
    
    print()


async def create_relationships_example(event_id, hazard_id, consequence_id):
    """创建关系示例"""
    print("=== 创建关系示例 ===")
    
    if not all([event_id, hazard_id, consequence_id]):
        print("✗ 缺少必要的节点ID")
        return
    
    try:
        # 创建隐患到事件的关系
        hazard_rel_data = RelationshipCreate(
            type="LEADS_TO",
            start_node=hazard_id,
            end_node=event_id,
            properties={
                "probability": 0.65,
                "conditions": ["湿度高", "负载过重"]
            }
        )
        
        hazard_rel_id = await graph_service.create_relationship(hazard_rel_data)
        print(f"✓ 创建隐患关系: {hazard_rel_id}")
        
        # 创建事件到后果的关系
        consequence_rel_id = await graph_service.create_causal_relationship(
            source_id=event_id,
            target_id=consequence_id,
            confidence=0.8,
            relation_type="导致"
        )
        print(f"✓ 创建因果关系: {consequence_rel_id}")
        
    except Exception as e:
        print(f"✗ 创建关系失败: {e}")
    
    print()


async def create_event_chain_example():
    """创建事件链示例"""
    print("=== 创建事件链示例 ===")
    
    try:
        # 创建事件链
        event_chain = EventChainCreate(
            source="电线老化",
            relation=RelationType.CAUSES,
            target="短路打火",
            confidence=0.85,
            timestamp=datetime.now(),
            context="老旧建筑电气线路，使用年限超过20年"
        )
        
        result = await graph_service.create_event_chain(event_chain)
        print(f"✓ 创建事件链成功:")
        print(f"  源节点ID: {result['source_node_id']}")
        print(f"  目标节点ID: {result['target_node_id']}")
        print(f"  关系ID: {result['relationship_id']}")
        
        # 创建更多事件链
        chains = [
            EventChainCreate(
                source="短路打火",
                relation=RelationType.CAUSES,
                target="引燃可燃物",
                confidence=0.75,
                context="电气短路产生火花"
            ),
            EventChainCreate(
                source="引燃可燃物",
                relation=RelationType.CAUSES,
                target="火势蔓延",
                confidence=0.90,
                context="可燃物被点燃后火势快速扩散"
            )
        ]
        
        batch_results = await graph_service.batch_create_event_chains(chains)
        print(f"✓ 批量创建事件链: {len(batch_results)} 个")
        
    except Exception as e:
        print(f"✗ 创建事件链失败: {e}")
    
    print()


async def query_examples():
    """查询示例"""
    print("=== 查询示例 ===")
    
    try:
        # 搜索节点
        search_results = await graph_service.search_nodes_by_description(
            search_text="电线",
            node_types=["FireEvent"],
            limit=5
        )
        print(f"✓ 搜索到 {len(search_results)} 个相关节点")
        
        for node in search_results:
            print(f"  - {node.id}: {node.properties.get('description', 'N/A')}")
        
        # 查找相似事件
        similar_events = await graph_service.find_similar_events(
            event_description="电气线路老化",
            limit=3
        )
        print(f"✓ 找到 {len(similar_events)} 个相似事件")
        
        # 执行自定义查询
        custom_query = """
        MATCH (h:Hazard)-[:LEADS_TO]->(e:FireEvent)-[:CAUSES]->(c:Consequence)
        RETURN h.description as hazard, e.description as event, c.description as consequence
        LIMIT 5
        """
        
        query_result = await graph_service.execute_cypher_query(custom_query)
        print(f"✓ 自定义查询返回 {query_result.record_count} 条记录")
        print(f"  执行时间: {query_result.execution_time:.2f}ms")
        
    except Exception as e:
        print(f"✗ 查询失败: {e}")
    
    print()


async def statistics_example():
    """统计信息示例"""
    print("=== 统计信息示例 ===")
    
    try:
        # 获取图统计信息
        stats = await graph_service.get_statistics()
        
        print(f"✓ 图统计信息:")
        print(f"  节点总数: {stats.node_count}")
        print(f"  关系总数: {stats.relationship_count}")
        print(f"  平均度数: {stats.avg_degree:.2f}")
        
        print(f"  节点类型分布:")
        for node_type, count in stats.node_type_distribution.items():
            print(f"    {node_type}: {count}")
        
        print(f"  关系类型分布:")
        for rel_type, count in stats.relationship_type_distribution.items():
            print(f"    {rel_type}: {count}")
        
        # 获取度数分布
        degree_dist = await graph_service.get_node_degree_distribution()
        print(f"  度数分布:")
        for degree, count in list(degree_dist.items())[:5]:  # 显示前5个
            print(f"    度数 {degree}: {count} 个节点")
        
    except Exception as e:
        print(f"✗ 获取统计信息失败: {e}")
    
    print()


async def cleanup_example():
    """清理示例数据"""
    print("=== 清理示例数据 ===")
    
    try:
        # 删除示例节点（这会同时删除相关关系）
        example_ids = [
            "example_event_001",
            "example_hazard_001", 
            "example_consequence_001"
        ]
        
        deleted_count = 0
        for node_id in example_ids:
            try:
                success = await graph_service.delete_node(node_id)
                if success:
                    deleted_count += 1
                    print(f"✓ 删除节点: {node_id}")
            except Exception:
                # 节点可能不存在，继续处理
                pass
        
        print(f"✓ 清理完成，删除了 {deleted_count} 个节点")
        
    except Exception as e:
        print(f"✗ 清理失败: {e}")
    
    print()


async def main():
    """主函数"""
    print("Neo4j 管理器使用示例")
    print("=" * 50)
    
    # 基础连接测试
    await basic_connection_example()
    
    # 创建节点
    event_id, hazard_id, consequence_id = await create_nodes_example()
    
    # 创建关系
    await create_relationships_example(event_id, hazard_id, consequence_id)
    
    # 创建事件链
    await create_event_chain_example()
    
    # 查询示例
    await query_examples()
    
    # 统计信息
    await statistics_example()
    
    # 清理示例数据
    await cleanup_example()
    
    print("所有示例运行完成！")


if __name__ == "__main__":
    asyncio.run(main())