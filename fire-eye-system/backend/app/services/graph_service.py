"""
图数据库服务层
提供高级的图操作接口
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.db.neo4j_manager import neo4j_manager
from app.schemas import (
    Node,
    Relationship,
    FireEventNode,
    HazardNode,
    ConsequenceNode,
    EventChain,
    EventChainCreate,
    NodeCreate,
    RelationshipCreate,
    GraphStatistics,
    QueryResult,
    Path,
    PathFindingQuery,
)

logger = logging.getLogger(__name__)


class GraphService:
    """图数据库服务"""
    
    def __init__(self):
        self.neo4j = neo4j_manager
    
    async def initialize(self) -> None:
        """初始化服务"""
        if not self.neo4j.driver:
            await self.neo4j.connect()
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            return await self.neo4j.ping()
        except Exception as e:
            logger.error(f"图数据库健康检查失败: {e}")
            return False
    
    # ===== 节点管理 =====
    
    async def create_fire_event(self, event: FireEventNode) -> str:
        """创建火灾事件节点"""
        try:
            node_id = await self.neo4j.create_fire_event_node(event)
            logger.info(f"创建火灾事件节点: {node_id}")
            return node_id
        except Exception as e:
            logger.error(f"创建火灾事件节点失败: {e}")
            raise
    
    async def create_hazard(self, hazard: HazardNode) -> str:
        """创建隐患节点"""
        try:
            node_id = await self.neo4j.create_hazard_node(hazard)
            logger.info(f"创建隐患节点: {node_id}")
            return node_id
        except Exception as e:
            logger.error(f"创建隐患节点失败: {e}")
            raise
    
    async def create_consequence(self, consequence: ConsequenceNode) -> str:
        """创建后果节点"""
        try:
            node_id = await self.neo4j.create_consequence_node(consequence)
            logger.info(f"创建后果节点: {node_id}")
            return node_id
        except Exception as e:
            logger.error(f"创建后果节点失败: {e}")
            raise
    
    async def get_node(self, node_id: str) -> Optional[Node]:
        """获取节点"""
        try:
            return await self.neo4j.get_node_by_id(node_id)
        except Exception as e:
            logger.error(f"获取节点失败: {node_id}, 错误: {e}")
            raise
    
    async def update_node(self, node_id: str, properties: Dict[str, Any]) -> bool:
        """更新节点"""
        try:
            return await self.neo4j.update_node(node_id, properties)
        except Exception as e:
            logger.error(f"更新节点失败: {node_id}, 错误: {e}")
            raise
    
    async def delete_node(self, node_id: str) -> bool:
        """删除节点"""
        try:
            return await self.neo4j.delete_node(node_id)
        except Exception as e:
            logger.error(f"删除节点失败: {node_id}, 错误: {e}")
            raise
    
    # ===== 关系管理 =====
    
    async def create_relationship(self, rel_data: RelationshipCreate) -> str:
        """创建关系"""
        try:
            rel_id = await self.neo4j.create_relationship(rel_data)
            logger.info(f"创建关系: {rel_id}")
            return rel_id
        except Exception as e:
            logger.error(f"创建关系失败: {e}")
            raise
    
    async def create_causal_relationship(
        self,
        source_id: str,
        target_id: str,
        confidence: float,
        relation_type: str = "导致"
    ) -> str:
        """创建因果关系"""
        try:
            rel_id = await self.neo4j.create_causal_relationship(
                source_id, target_id, confidence, relation_type
            )
            logger.info(f"创建因果关系: {source_id} -> {target_id}")
            return rel_id
        except Exception as e:
            logger.error(f"创建因果关系失败: {e}")
            raise
    
    async def get_relationship(self, rel_id: str) -> Optional[Relationship]:
        """获取关系"""
        try:
            return await self.neo4j.get_relationship_by_id(rel_id)
        except Exception as e:
            logger.error(f"获取关系失败: {rel_id}, 错误: {e}")
            raise
    
    async def delete_relationship(self, rel_id: str) -> bool:
        """删除关系"""
        try:
            return await self.neo4j.delete_relationship(rel_id)
        except Exception as e:
            logger.error(f"删除关系失败: {rel_id}, 错误: {e}")
            raise
    
    # ===== 事件链管理 =====
    
    async def create_event_chain(self, event_chain: EventChainCreate) -> Dict[str, str]:
        """创建事件链"""
        try:
            # 转换为 EventChain 对象
            chain = EventChain(
                source=event_chain.source,
                relation=event_chain.relation,
                target=event_chain.target,
                confidence=event_chain.confidence,
                timestamp=event_chain.timestamp,
                context=event_chain.context or ""
            )
            
            result = await self.neo4j.create_event_chain(chain)
            logger.info(f"创建事件链: {event_chain.source} -> {event_chain.target}")
            return result
        except Exception as e:
            logger.error(f"创建事件链失败: {e}")
            raise
    
    async def batch_create_event_chains(self, event_chains: List[EventChainCreate]) -> List[Dict[str, str]]:
        """批量创建事件链"""
        if not event_chains:
            return []

        normalized_chains = [
            EventChain(
                source=chain.source,
                relation=chain.relation,
                target=chain.target,
                confidence=chain.confidence,
                timestamp=chain.timestamp,
                context=chain.context or "",
            )
            for chain in event_chains
        ]

        try:
            results = await self.neo4j.batch_create_event_chains(normalized_chains)
            logger.info(f"批量创建事件链完成: {len(results)}/{len(event_chains)}")
            return results
        except Exception as e:
            logger.error(f"批量写入事件链失败，回退为逐条写入: {e}")

        results = []
        for chain in event_chains:
            try:
                result = await self.create_event_chain(chain)
                results.append(result)
            except Exception as e:
                logger.error(f"批量创建事件链失败: {chain.source} -> {chain.target}, 错误: {e}")
                continue

        logger.info(f"回退逐条创建事件链完成: {len(results)}/{len(event_chains)}")
        return results
    
    # ===== 查询操作 =====
    
    async def execute_cypher_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        """执行 Cypher 查询"""
        try:
            start_time = datetime.now()
            records = await self.neo4j.execute_query(query, parameters)
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return QueryResult(
                records=records,
                summary={"query": query, "parameters": parameters},
                execution_time=execution_time,
                record_count=len(records)
            )
        except Exception as e:
            logger.error(f"执行 Cypher 查询失败: {query}, 错误: {e}")
            raise
    
    async def find_paths(self, query: PathFindingQuery) -> List[Path]:
        """查找路径"""
        try:
            return await self.neo4j.find_paths(
                start_node=query.start_node,
                end_node=query.end_node,
                max_depth=query.max_depth,
                relationship_types=query.relationship_types
            )
        except Exception as e:
            logger.error(f"路径查找失败: {e}")
            raise
    
    async def get_node_neighbors(
        self,
        node_id: str,
        direction: str = "OUTGOING",
        relationship_types: Optional[List[str]] = None
    ) -> List[Node]:
        """获取节点邻居"""
        try:
            return await self.neo4j.get_node_neighbors(
                node_id, direction, relationship_types
            )
        except Exception as e:
            logger.error(f"获取节点邻居失败: {node_id}, 错误: {e}")
            raise
    
    # ===== 搜索功能 =====
    
    async def query_graph(self, query_text: str) -> List[dict]:
        """
        查询图数据库（用于聊天接口）
        
        Args:
            query_text: 查询文本
            
        Returns:
            查询结果列表
        """
        try:
            # 使用文本搜索节点
            nodes = await self.search_nodes_by_description(
                search_text=query_text,
                limit=10
            )
            
            # 转换为字典格式
            results = []
            for node in nodes:
                # 清理 properties，确保所有值都可以序列化
                clean_properties = {}
                for key, value in node.properties.items():
                    if hasattr(value, 'to_native'):
                        # Neo4j DateTime 对象
                        clean_properties[key] = value.to_native().isoformat()
                    elif isinstance(value, datetime):
                        clean_properties[key] = value.isoformat()
                    else:
                        clean_properties[key] = value
                
                result = {
                    "id": node.id,
                    "type": node.labels[0] if node.labels else "Unknown",
                    "properties": clean_properties,
                    "description": clean_properties.get("description", ""),
                    "name": clean_properties.get("standard_term", clean_properties.get("id", node.id))
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"查询图数据库失败: {e}")
            return []
    
    async def search_nodes_by_description(
        self,
        search_text: str,
        node_types: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Node]:
        """根据描述搜索节点"""
        try:
            # 构建标签过滤
            if node_types:
                label_filter = "|".join(node_types)
                node_pattern = f"(n:{label_filter})"
            else:
                node_pattern = "(n)"
            
            # 使用更宽松的搜索条件，只检查存在的字段
            query = f"""
            MATCH {node_pattern}
            WHERE toLower(toString(n.description)) CONTAINS toLower($search_text)
               OR toLower(toString(n.standard_term)) CONTAINS toLower($search_text)
               OR toLower(toString(n.id)) CONTAINS toLower($search_text)
               OR toLower(toString(n.category)) CONTAINS toLower($search_text)
            RETURN n, labels(n) as labels
            LIMIT $limit
            """
            
            results = await self.neo4j.execute_query(
                query,
                {"search_text": search_text, "limit": limit}
            )
            
            # 如果没有结果，返回所有节点（限制数量）
            if not results:
                logger.info(f"未找到匹配的节点，返回所有节点")
                query = f"""
                MATCH {node_pattern}
                RETURN n, labels(n) as labels
                LIMIT $limit
                """
                results = await self.neo4j.execute_query(
                    query,
                    {"limit": limit}
                )
            
            nodes = []
            for result in results:
                node_data = result["n"]
                labels = result["labels"]
                
                # 处理日期时间字段
                created_at = node_data.get("created_at")
                updated_at = node_data.get("updated_at")
                
                # 如果是 neo4j.time.DateTime 对象，转换为 datetime
                if hasattr(created_at, 'to_native'):
                    created_at = created_at.to_native()
                elif isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at)
                else:
                    created_at = datetime.now()
                
                if hasattr(updated_at, 'to_native'):
                    updated_at = updated_at.to_native()
                elif isinstance(updated_at, str):
                    updated_at = datetime.fromisoformat(updated_at)
                else:
                    updated_at = datetime.now()
                
                node = Node(
                    id=node_data["id"],
                    labels=labels,
                    properties=dict(node_data),
                    created_at=created_at,
                    updated_at=updated_at
                )
                nodes.append(node)
            
            return nodes
        except Exception as e:
            logger.error(f"搜索节点失败: {search_text}, 错误: {e}")
            raise
    
    async def find_similar_events(
        self,
        event_description: str,
        similarity_threshold: float = 0.7,
        limit: int = 10
    ) -> List[Node]:
        """查找相似事件"""
        try:
            # 简化版本：基于关键词匹配
            # 实际实现可以使用向量相似度或全文搜索
            keywords = event_description.split()
            
            conditions = []
            for keyword in keywords[:3]:  # 限制关键词数量
                conditions.append(f"n.description CONTAINS '{keyword}'")
            
            if not conditions:
                return []
            
            where_clause = " OR ".join(conditions)
            
            query = f"""
            MATCH (n:FireEvent)
            WHERE {where_clause}
            RETURN n, labels(n) as labels
            LIMIT $limit
            """
            
            results = await self.neo4j.execute_query(
                query,
                {"limit": limit}
            )
            
            nodes = []
            for result in results:
                node_data = result["n"]
                labels = result["labels"]
                
                node = Node(
                    id=node_data["id"],
                    labels=labels,
                    properties=dict(node_data),
                    created_at=datetime.fromisoformat(node_data.get("created_at", datetime.now().isoformat())),
                    updated_at=datetime.fromisoformat(node_data.get("updated_at", datetime.now().isoformat()))
                )
                nodes.append(node)
            
            return nodes
        except Exception as e:
            logger.error(f"查找相似事件失败: {event_description}, 错误: {e}")
            raise
    
    # ===== 统计信息 =====
    
    async def get_statistics(self) -> GraphStatistics:
        """获取图统计信息"""
        try:
            return await self.neo4j.get_graph_statistics()
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            raise
    
    async def get_node_degree_distribution(self) -> Dict[str, int]:
        """获取节点度数分布"""
        try:
            query = """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]-()
            WITH n, count(r) as degree
            RETURN degree, count(n) as node_count
            ORDER BY degree
            """
            
            results = await self.neo4j.execute_query(query)
            
            distribution = {}
            for result in results:
                degree = result["degree"]
                count = result["node_count"]
                distribution[str(degree)] = count
            
            return distribution
        except Exception as e:
            logger.error(f"获取度数分布失败: {e}")
            raise
    
    # ===== 数据导入导出 =====
    
    async def export_subgraph(
        self,
        node_ids: List[str],
        include_relationships: bool = True
    ) -> Dict[str, Any]:
        """导出子图"""
        try:
            # 获取指定节点
            nodes_query = """
            MATCH (n)
            WHERE n.id IN $node_ids
            RETURN n, labels(n) as labels
            """
            
            node_results = await self.neo4j.execute_query(
                nodes_query,
                {"node_ids": node_ids}
            )
            
            nodes = []
            for result in node_results:
                node_data = result["n"]
                labels = result["labels"]
                nodes.append({
                    "id": node_data["id"],
                    "labels": labels,
                    "properties": dict(node_data)
                })
            
            relationships = []
            if include_relationships:
                # 获取节点间的关系
                rels_query = """
                MATCH (a)-[r]->(b)
                WHERE a.id IN $node_ids AND b.id IN $node_ids
                RETURN r, type(r) as rel_type, a.id as start_id, b.id as end_id
                """
                
                rel_results = await self.neo4j.execute_query(
                    rels_query,
                    {"node_ids": node_ids}
                )
                
                for result in rel_results:
                    rel_data = result["r"]
                    relationships.append({
                        "id": rel_data["id"],
                        "type": result["rel_type"],
                        "start_node": result["start_id"],
                        "end_node": result["end_id"],
                        "properties": dict(rel_data)
                    })
            
            return {
                "nodes": nodes,
                "relationships": relationships,
                "export_time": datetime.now().isoformat(),
                "node_count": len(nodes),
                "relationship_count": len(relationships)
            }
        except Exception as e:
            logger.error(f"导出子图失败: {e}")
            raise


# 全局图服务实例
graph_service = GraphService()
