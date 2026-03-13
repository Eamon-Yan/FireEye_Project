"""
Neo4j 管理器测试
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.db.neo4j_manager import Neo4jManager
from app.schemas import (
    NodeCreate,
    RelationshipCreate,
    FireEventNode,
    EventType,
    HazardNode,
    RiskLevel,
    EventChain,
    RelationType,
)


class TestNeo4jManager:
    """Neo4j 管理器测试"""
    
    @pytest.fixture
    def neo4j_manager(self):
        """创建 Neo4j 管理器实例"""
        manager = Neo4jManager()
        # 模拟驱动
        manager.driver = AsyncMock()
        return manager
    
    @pytest.mark.asyncio
    async def test_ping_success(self, neo4j_manager):
        """测试连接测试成功"""
        # 模拟成功的连接验证
        neo4j_manager.driver.verify_connectivity = AsyncMock()
        
        result = await neo4j_manager.ping()
        
        assert result is True
        neo4j_manager.driver.verify_connectivity.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ping_failure(self, neo4j_manager):
        """测试连接测试失败"""
        # 模拟连接验证失败
        neo4j_manager.driver.verify_connectivity = AsyncMock(
            side_effect=Exception("连接失败")
        )
        
        with pytest.raises(ConnectionError):
            await neo4j_manager.ping()
    
    @pytest.mark.asyncio
    async def test_create_node_success(self, neo4j_manager):
        """测试创建节点成功"""
        # 模拟会话和查询结果
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.data.return_value = [{"node_id": "test_node_001"}]
        mock_session.run.return_value = mock_result
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        
        neo4j_manager.driver.session.return_value = mock_session
        
        node_data = NodeCreate(
            labels=["FireEvent"],
            properties={
                "description": "测试事件",
                "category": "测试分类"
            }
        )
        
        # 由于实际方法使用 execute_query，我们需要模拟它
        neo4j_manager.execute_query = AsyncMock(
            return_value={"node_id": "test_node_001"}
        )
        
        result = await neo4j_manager.create_node(node_data)
        
        assert result == "test_node_001"
    
    @pytest.mark.asyncio
    async def test_create_fire_event_node(self, neo4j_manager):
        """测试创建火灾事件节点"""
        # 模拟 create_node 方法
        neo4j_manager.create_node = AsyncMock(return_value="event_001")
        
        event = FireEventNode(
            id="event_001",
            event_type=EventType.CAUSE,
            description="电线老化",
            standard_term="电气线路老化",
            category="电气火灾",
            severity_level=5,
            frequency=10
        )
        
        result = await neo4j_manager.create_fire_event_node(event)
        
        assert result == "event_001"
        neo4j_manager.create_node.assert_called_once()
        
        # 验证调用参数
        call_args = neo4j_manager.create_node.call_args[0][0]
        assert call_args.labels == ["FireEvent"]
        assert call_args.properties["description"] == "电线老化"
        assert call_args.properties["event_type"] == "原因"
    
    @pytest.mark.asyncio
    async def test_create_hazard_node(self, neo4j_manager):
        """测试创建隐患节点"""
        # 模拟 create_node 方法
        neo4j_manager.create_node = AsyncMock(return_value="hazard_001")
        
        hazard = HazardNode(
            id="hazard_001",
            description="老旧电气线路",
            risk_level=RiskLevel.HIGH,
            location="居民区"
        )
        
        result = await neo4j_manager.create_hazard_node(hazard)
        
        assert result == "hazard_001"
        neo4j_manager.create_node.assert_called_once()
        
        # 验证调用参数
        call_args = neo4j_manager.create_node.call_args[0][0]
        assert call_args.labels == ["Hazard"]
        assert call_args.properties["risk_level"] == "高"
    
    @pytest.mark.asyncio
    async def test_create_relationship_success(self, neo4j_manager):
        """测试创建关系成功"""
        # 模拟 execute_query 方法
        neo4j_manager.execute_query = AsyncMock(
            return_value={"rel_id": "rel_001"}
        )
        
        rel_data = RelationshipCreate(
            type="CAUSES",
            start_node="event_001",
            end_node="event_002",
            properties={"confidence": 0.8}
        )
        
        result = await neo4j_manager.create_relationship(rel_data)
        
        assert result == "rel_001"
        neo4j_manager.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_causal_relationship(self, neo4j_manager):
        """测试创建因果关系"""
        # 模拟 create_relationship 方法
        neo4j_manager.create_relationship = AsyncMock(return_value="rel_001")
        
        result = await neo4j_manager.create_causal_relationship(
            source_id="event_001",
            target_id="event_002",
            confidence=0.85,
            relation_type="导致"
        )
        
        assert result == "rel_001"
        neo4j_manager.create_relationship.assert_called_once()
        
        # 验证调用参数
        call_args = neo4j_manager.create_relationship.call_args[0][0]
        assert call_args.type == "CAUSES"
        assert call_args.start_node == "event_001"
        assert call_args.end_node == "event_002"
        assert call_args.properties["confidence"] == 0.85
    
    @pytest.mark.asyncio
    async def test_create_event_chain(self, neo4j_manager):
        """测试创建事件链"""
        # 模拟相关方法
        neo4j_manager._get_or_create_event_node = AsyncMock(
            side_effect=["event_001", "event_002"]
        )
        neo4j_manager.create_causal_relationship = AsyncMock(
            return_value="rel_001"
        )
        
        event_chain = EventChain(
            source="电线老化",
            relation=RelationType.CAUSES,
            target="短路打火",
            confidence=0.85,
            context="测试上下文"
        )
        
        result = await neo4j_manager.create_event_chain(event_chain)
        
        assert result["source_node_id"] == "event_001"
        assert result["target_node_id"] == "event_002"
        assert result["relationship_id"] == "rel_001"
    
    @pytest.mark.asyncio
    async def test_get_or_create_event_node_existing(self, neo4j_manager):
        """测试获取现有事件节点"""
        # 模拟查询返回现有节点
        neo4j_manager.execute_query = AsyncMock(
            return_value={"node_id": "existing_event_001"}
        )
        
        result = await neo4j_manager._get_or_create_event_node("电线老化")
        
        assert result == "existing_event_001"
    
    @pytest.mark.asyncio
    async def test_get_or_create_event_node_new(self, neo4j_manager):
        """测试创建新事件节点"""
        # 模拟查询返回空结果（节点不存在）
        neo4j_manager.execute_query = AsyncMock(return_value={})
        # 模拟创建新节点
        neo4j_manager.create_fire_event_node = AsyncMock(
            return_value="new_event_001"
        )
        
        result = await neo4j_manager._get_or_create_event_node("新事件")
        
        assert result == "new_event_001"
        neo4j_manager.create_fire_event_node.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_graph_statistics(self, neo4j_manager):
        """测试获取图统计信息"""
        # 模拟统计查询结果
        neo4j_manager.execute_query = AsyncMock(
            side_effect=[
                {"count": 100},  # 节点总数
                {"count": 150},  # 关系总数
                [  # 节点类型分布
                    {"labels": ["FireEvent"], "count": 60},
                    {"labels": ["Hazard"], "count": 25},
                    {"labels": ["Consequence"], "count": 15}
                ],
                [  # 关系类型分布
                    {"rel_type": "CAUSES", "count": 80},
                    {"rel_type": "LEADS_TO", "count": 40},
                    {"rel_type": "RESULTS_IN", "count": 30}
                ]
            ]
        )
        
        stats = await neo4j_manager.get_graph_statistics()
        
        assert stats.node_count == 100
        assert stats.relationship_count == 150
        assert stats.node_type_distribution["FireEvent"] == 60
        assert stats.relationship_type_distribution["CAUSES"] == 80
        assert stats.avg_degree == 3.0  # (150 * 2) / 100


class TestNeo4jManagerIntegration:
    """Neo4j 管理器集成测试（需要真实数据库）"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_connection(self):
        """测试真实数据库连接"""
        # 这个测试需要真实的 Neo4j 数据库
        # 在 CI/CD 环境中可能需要跳过
        manager = Neo4jManager()
        
        try:
            await manager.connect()
            result = await manager.ping()
            assert result is True
        except Exception:
            pytest.skip("需要真实的 Neo4j 数据库连接")
        finally:
            await manager.disconnect()


if __name__ == "__main__":
    pytest.main([__file__])