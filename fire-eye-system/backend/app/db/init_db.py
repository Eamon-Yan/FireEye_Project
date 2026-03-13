"""
数据库初始化脚本
"""

import logging
from typing import List

from app.db.neo4j_client import neo4j_client
from app.db.redis_client import redis_client

logger = logging.getLogger(__name__)


async def create_sample_data() -> None:
    """创建示例数据"""
    
    # 示例火灾事件节点
    sample_fire_events = [
        {
            "id": "event_001",
            "event_type": "原因",
            "description": "电线老化",
            "standard_term": "电气线路老化",
            "category": "电气火灾",
            "severity_level": 3,
            "frequency": 15
        },
        {
            "id": "event_002", 
            "event_type": "过程",
            "description": "短路打火",
            "standard_term": "电气短路",
            "category": "电气火灾",
            "severity_level": 4,
            "frequency": 12
        },
        {
            "id": "event_003",
            "event_type": "过程", 
            "description": "引燃可燃物",
            "standard_term": "可燃物引燃",
            "category": "燃烧过程",
            "severity_level": 5,
            "frequency": 8
        },
        {
            "id": "event_004",
            "event_type": "结果",
            "description": "火势蔓延",
            "standard_term": "火灾蔓延",
            "category": "火灾发展",
            "severity_level": 6,
            "frequency": 6
        }
    ]
    
    # 示例隐患节点
    sample_hazards = [
        {
            "id": "hazard_001",
            "description": "老旧建筑电气线路",
            "risk_level": "高",
            "location": "居民区"
        },
        {
            "id": "hazard_002", 
            "description": "电动车充电设施",
            "risk_level": "中",
            "location": "地下车库"
        }
    ]
    
    # 示例后果节点
    sample_consequences = [
        {
            "id": "consequence_001",
            "description": "人员伤亡",
            "impact_level": "严重",
            "affected_area": "整栋建筑"
        },
        {
            "id": "consequence_002",
            "description": "财产损失", 
            "impact_level": "重大",
            "affected_area": "多个房间"
        }
    ]
    
    try:
        # 创建火灾事件节点
        for event in sample_fire_events:
            query = """
            MERGE (e:FireEvent {id: $id})
            SET e.event_type = $event_type,
                e.description = $description,
                e.standard_term = $standard_term,
                e.category = $category,
                e.severity_level = $severity_level,
                e.frequency = $frequency,
                e.created_at = datetime(),
                e.updated_at = datetime()
            """
            await neo4j_client.execute_write_transaction(query, event)
        
        # 创建隐患节点
        for hazard in sample_hazards:
            query = """
            MERGE (h:Hazard {id: $id})
            SET h.description = $description,
                h.risk_level = $risk_level,
                h.location = $location,
                h.created_at = datetime(),
                h.updated_at = datetime()
            """
            await neo4j_client.execute_write_transaction(query, hazard)
        
        # 创建后果节点
        for consequence in sample_consequences:
            query = """
            MERGE (c:Consequence {id: $id})
            SET c.description = $description,
                c.impact_level = $impact_level,
                c.affected_area = $affected_area,
                c.created_at = datetime(),
                c.updated_at = datetime()
            """
            await neo4j_client.execute_write_transaction(query, consequence)
        
        # 创建因果关系
        causal_relations = [
            {
                "source": "event_001",
                "target": "event_002", 
                "relation_type": "导致",
                "confidence": 0.85,
                "time_delay": 300  # 5分钟
            },
            {
                "source": "event_002",
                "target": "event_003",
                "relation_type": "导致", 
                "confidence": 0.75,
                "time_delay": 120  # 2分钟
            },
            {
                "source": "event_003",
                "target": "event_004",
                "relation_type": "导致",
                "confidence": 0.90,
                "time_delay": 600  # 10分钟
            }
        ]
        
        for relation in causal_relations:
            query = """
            MATCH (source:FireEvent {id: $source})
            MATCH (target:FireEvent {id: $target})
            MERGE (source)-[r:CAUSES]->(target)
            SET r.id = $source + '_causes_' + $target,
                r.relation_type = $relation_type,
                r.confidence = $confidence,
                r.time_delay = $time_delay,
                r.created_at = datetime()
            """
            await neo4j_client.execute_write_transaction(query, relation)
        
        # 创建隐患到事件的关系
        hazard_relations = [
            {
                "hazard": "hazard_001",
                "event": "event_001",
                "probability": 0.65,
                "conditions": ["湿度高", "负载过重"]
            },
            {
                "hazard": "hazard_002", 
                "event": "event_001",
                "probability": 0.45,
                "conditions": ["充电时间过长", "设备老化"]
            }
        ]
        
        for relation in hazard_relations:
            query = """
            MATCH (h:Hazard {id: $hazard})
            MATCH (e:FireEvent {id: $event})
            MERGE (h)-[r:LEADS_TO]->(e)
            SET r.id = $hazard + '_leads_to_' + $event,
                r.probability = $probability,
                r.conditions = $conditions,
                r.created_at = datetime()
            """
            await neo4j_client.execute_write_transaction(query, relation)
        
        # 创建事件到后果的关系
        consequence_relations = [
            {
                "event": "event_004",
                "consequence": "consequence_001",
                "severity": 8,
                "likelihood": 0.70
            },
            {
                "event": "event_004",
                "consequence": "consequence_002", 
                "severity": 6,
                "likelihood": 0.85
            }
        ]
        
        for relation in consequence_relations:
            query = """
            MATCH (e:FireEvent {id: $event})
            MATCH (c:Consequence {id: $consequence})
            MERGE (e)-[r:RESULTS_IN]->(c)
            SET r.id = $event + '_results_in_' + $consequence,
                r.severity = $severity,
                r.likelihood = $likelihood,
                r.created_at = datetime()
            """
            await neo4j_client.execute_write_transaction(query, relation)
        
        logger.info("示例数据创建成功")
        
    except Exception as e:
        logger.error(f"创建示例数据失败: {e}")
        raise


async def init_terminology_mapping() -> None:
    """初始化术语映射缓存"""
    
    # 示例术语映射数据
    terminology_mappings = {
        "电瓶车自燃": "电动自行车火灾",
        "电池爆燃": "电动自行车火灾", 
        "线路老化": "电气线路老化",
        "电线老化": "电气线路老化",
        "短路": "电气短路",
        "短路打火": "电气短路",
        "漏电": "电气漏电",
        "过载": "电气过载",
        "火势扩散": "火灾蔓延",
        "火势蔓延": "火灾蔓延",
        "烟雾扩散": "烟气蔓延",
        "烟气传播": "烟气蔓延"
    }
    
    try:
        # 将术语映射存储到 Redis
        for original_term, standard_term in terminology_mappings.items():
            mapping_data = {
                "standard_term": standard_term,
                "confidence": 0.95,
                "category": "火灾事件"
            }
            await redis_client.set_hash(
                "terminology_mapping",
                original_term,
                mapping_data
            )
        
        logger.info("术语映射缓存初始化成功")
        
    except Exception as e:
        logger.error(f"初始化术语映射失败: {e}")
        raise


async def initialize_database() -> None:
    """初始化数据库"""
    
    logger.info("开始初始化数据库...")
    
    try:
        # 连接数据库
        await neo4j_client.connect()
        await redis_client.connect()
        
        # 创建约束和索引
        await neo4j_client.create_constraints_and_indexes()
        
        # 检查是否已有数据
        result = await neo4j_client.execute_read_transaction(
            "MATCH (n) RETURN count(n) as node_count"
        )
        
        node_count = result[0]["node_count"] if result else 0
        
        if node_count == 0:
            # 创建示例数据
            await create_sample_data()
            logger.info("数据库为空，已创建示例数据")
        else:
            logger.info(f"数据库已有 {node_count} 个节点，跳过示例数据创建")
        
        # 初始化术语映射
        await init_terminology_mapping()
        
        logger.info("数据库初始化完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


async def cleanup_database() -> None:
    """清理数据库连接"""
    
    try:
        await neo4j_client.disconnect()
        await redis_client.disconnect()
        logger.info("数据库连接已清理")
        
    except Exception as e:
        logger.error(f"清理数据库连接失败: {e}")


if __name__ == "__main__":
    import asyncio
    
    async def main():
        await initialize_database()
        await cleanup_database()
    
    asyncio.run(main())