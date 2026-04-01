"""
Neo4j 数据库管理器
集成 Pydantic schemas 的高级数据访问层
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import uuid

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import ServiceUnavailable, AuthError, ClientError

from app.core.config import settings
from app.schemas import (
    Node,
    Relationship,
    FireEventNode,
    HazardNode,
    ConsequenceNode,
    NodeCreate,
    RelationshipCreate,
    EventChain,
    QueryResult,
    GraphStatistics,
    Path,
)

logger = logging.getLogger(__name__)


class Neo4jManager:
    """Neo4j 数据库管理器"""
    
    def __init__(self):
        self.driver: Optional[AsyncDriver] = None
        self.uri = settings.NEO4J_URI
        self.username = settings.NEO4J_USERNAME
        self.password = settings.NEO4J_PASSWORD
        self.database = settings.NEO4J_DATABASE
        
        logger.info(f"Neo4j Manager initialized with URI: {self.uri}")
    
    async def connect(self) -> None:
        """建立数据库连接"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60,
            )
            
            # 验证连接
            await self.ping()
            logger.info("Neo4j 数据库连接成功")
            
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Neo4j 连接失败: {e}")
            raise ConnectionError(f"无法连接到 Neo4j 数据库: {e}")
        except Exception as e:
            logger.error(f"Neo4j 连接异常: {e}")
            raise
    
    async def disconnect(self) -> None:
        """关闭数据库连接"""
        if self.driver:
            await self.driver.close()
            self.driver = None
            logger.info("Neo4j 数据库连接已关闭")
    
    async def ping(self) -> bool:
        """测试数据库连接"""
        if not self.driver:
            raise RuntimeError("数据库驱动未初始化")
        
        try:
            await self.driver.verify_connectivity()
            logger.debug("Neo4j 连接测试成功")
            return True
        except Exception as e:
            logger.error(f"Neo4j 连接测试失败: {e}")
            raise ConnectionError(f"数据库连接测试失败: {e}")
    
    async def get_session(self) -> AsyncSession:
        """获取数据库会话"""
        if not self.driver:
            await self.connect()
        
        return self.driver.session(database=self.database)
    
    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        fetch_all: bool = True
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """执行 Cypher 查询"""
        if parameters is None:
            parameters = {}
        
        start_time = datetime.now()
        
        async with await self.get_session() as session:
            try:
                result = await session.run(query, parameters)
                
                if fetch_all:
                    records = await result.data()
                    execution_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    logger.debug(f"查询执行完成: {len(records)} 条记录, 耗时: {execution_time:.2f}ms")
                    return records
                else:
                    record = await result.single()
                    execution_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    logger.debug(f"查询执行完成: 单条记录, 耗时: {execution_time:.2f}ms")
                    return record.data() if record else {}
                    
            except ClientError as e:
                logger.error(f"Cypher 查询错误: {query}, 参数: {parameters}, 错误: {e}")
                raise ValueError(f"查询语法错误: {e}")
            except Exception as e:
                logger.error(f"查询执行失败: {query}, 错误: {e}")
                raise
    
    # ===== 节点操作 =====
    
    async def create_node(self, node_data: NodeCreate) -> str:
        """创建节点"""
        node_id = str(uuid.uuid4())
        labels_str = ":".join(node_data.labels)
        
        # 添加时间戳
        properties = node_data.properties.copy()
        properties.update({
            "id": node_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })
        
        query = f"""
        CREATE (n:{labels_str})
        SET n = $properties
        RETURN n.id as node_id
        """
        
        result = await self.execute_query(
            query, 
            {"properties": properties}, 
            fetch_all=False
        )
        
        logger.info(f"创建节点成功: {node_id}, 标签: {node_data.labels}")
        return result["node_id"]
    
    async def create_fire_event_node(self, event: FireEventNode) -> str:
        """创建火灾事件节点"""
        node_data = NodeCreate(
            labels=["FireEvent"],
            properties={
                "event_type": event.event_type,
                "description": event.description,
                "standard_term": event.standard_term,
                "category": event.category,
                "severity_level": event.severity_level,
                "frequency": event.frequency
            }
        )
        
        if hasattr(event, 'id') and event.id:
            node_data.properties["id"] = event.id
            
        return await self.create_node(node_data)
    
    async def create_hazard_node(self, hazard: HazardNode) -> str:
        """创建隐患节点"""
        node_data = NodeCreate(
            labels=["Hazard"],
            properties={
                "description": hazard.description,
                "standard_term": hazard.standard_term,
                "risk_level": hazard.risk_level,
                "location": hazard.location
            }
        )
        
        if hasattr(hazard, 'id') and hazard.id:
            node_data.properties["id"] = hazard.id
            
        return await self.create_node(node_data)
    
    async def create_consequence_node(self, consequence: ConsequenceNode) -> str:
        """创建后果节点"""
        node_data = NodeCreate(
            labels=["Consequence"],
            properties={
                "description": consequence.description,
                "standard_term": consequence.standard_term,
                "impact_level": consequence.impact_level,
                "affected_area": consequence.affected_area
            }
        )
        
        if hasattr(consequence, 'id') and consequence.id:
            node_data.properties["id"] = consequence.id
            
        return await self.create_node(node_data)
    
    async def get_node_by_id(self, node_id: str) -> Optional[Node]:
        """根据ID获取节点"""
        query = """
        MATCH (n {id: $node_id})
        RETURN n, labels(n) as labels
        """
        
        result = await self.execute_query(
            query, 
            {"node_id": node_id}, 
            fetch_all=False
        )
        
        if not result:
            return None
        
        node_data = result["n"]
        labels = result["labels"]
        
        return Node(
            id=node_data["id"],
            labels=labels,
            properties=dict(node_data),
            created_at=datetime.fromisoformat(node_data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(node_data.get("updated_at", datetime.now().isoformat()))
        )
    
    async def update_node(self, node_id: str, properties: Dict[str, Any]) -> bool:
        """更新节点属性"""
        # 添加更新时间戳
        properties = properties.copy()
        properties["updated_at"] = datetime.now().isoformat()
        
        query = """
        MATCH (n {id: $node_id})
        SET n += $properties
        RETURN n.id as updated_id
        """
        
        result = await self.execute_query(
            query,
            {"node_id": node_id, "properties": properties},
            fetch_all=False
        )
        
        success = bool(result.get("updated_id"))
        if success:
            logger.info(f"更新节点成功: {node_id}")
        else:
            logger.warning(f"节点不存在: {node_id}")
            
        return success
    
    async def delete_node(self, node_id: str) -> bool:
        """删除节点及其关系"""
        query = """
        MATCH (n {id: $node_id})
        DETACH DELETE n
        RETURN count(n) as deleted_count
        """
        
        result = await self.execute_query(
            query,
            {"node_id": node_id},
            fetch_all=False
        )
        
        deleted_count = result.get("deleted_count", 0)
        success = deleted_count > 0
        
        if success:
            logger.info(f"删除节点成功: {node_id}")
        else:
            logger.warning(f"节点不存在: {node_id}")
            
        return success
    
    # ===== 关系操作 =====
    
    async def create_relationship(self, rel_data: RelationshipCreate) -> str:
        """创建关系"""
        rel_id = str(uuid.uuid4())
        
        # 添加时间戳和ID
        properties = rel_data.properties.copy()
        properties.update({
            "id": rel_id,
            "created_at": datetime.now().isoformat()
        })
        
        query = f"""
        MATCH (start {{id: $start_node}})
        MATCH (end {{id: $end_node}})
        CREATE (start)-[r:{rel_data.type}]->(end)
        SET r = $properties
        RETURN r.id as rel_id
        """
        
        result = await self.execute_query(
            query,
            {
                "start_node": rel_data.start_node,
                "end_node": rel_data.end_node,
                "properties": properties
            },
            fetch_all=False
        )
        
        logger.info(f"创建关系成功: {rel_id}, 类型: {rel_data.type}")
        return result["rel_id"]
    
    async def create_causal_relationship(
        self,
        source_id: str,
        target_id: str,
        confidence: float,
        relation_type: str = "导致",
        time_delay: Optional[int] = None,
        relationship_label: str = "CAUSES"
    ) -> str:
        """创建因果关系"""
        properties = {
            "relation_type": relation_type,
            "confidence": confidence
        }
        
        if time_delay is not None:
            properties["time_delay"] = time_delay
        
        rel_data = RelationshipCreate(
            type=relationship_label,
            start_node=source_id,
            end_node=target_id,
            properties=properties
        )
        
        return await self.create_relationship(rel_data)
    
    async def get_relationship_by_id(self, rel_id: str) -> Optional[Relationship]:
        """根据ID获取关系"""
        query = """
        MATCH ()-[r {id: $rel_id}]->()
        RETURN r, type(r) as rel_type, startNode(r).id as start_id, endNode(r).id as end_id
        """
        
        result = await self.execute_query(
            query,
            {"rel_id": rel_id},
            fetch_all=False
        )
        
        if not result:
            return None
        
        rel_data = result["r"]
        
        return Relationship(
            id=rel_data["id"],
            type=result["rel_type"],
            start_node=result["start_id"],
            end_node=result["end_id"],
            properties=dict(rel_data),
            weight=rel_data.get("weight", 1.0),
            created_at=datetime.fromisoformat(rel_data.get("created_at", datetime.now().isoformat()))
        )
    
    async def delete_relationship(self, rel_id: str) -> bool:
        """删除关系"""
        query = """
        MATCH ()-[r {id: $rel_id}]->()
        DELETE r
        RETURN count(r) as deleted_count
        """
        
        result = await self.execute_query(
            query,
            {"rel_id": rel_id},
            fetch_all=False
        )
        
        deleted_count = result.get("deleted_count", 0)
        success = deleted_count > 0
        
        if success:
            logger.info(f"删除关系成功: {rel_id}")
        else:
            logger.warning(f"关系不存在: {rel_id}")
            
        return success
    
    # ===== 事件链操作 =====
    
    async def create_event_chain(self, event_chain: EventChain) -> Dict[str, str]:
        """从事件链创建节点和关系"""
        # 创建或获取源节点
        source_node_id, source_node_label = await self._get_or_create_event_node(event_chain.source)
        
        # 创建或获取目标节点
        target_node_id, target_node_label = await self._get_or_create_event_node(event_chain.target)
        
        relationship_label = self._determine_relationship_label(source_node_label, target_node_label)
        
        # 创建关系
        rel_id = await self.create_causal_relationship(
            source_node_id,
            target_node_id,
            event_chain.confidence,
            event_chain.relation,
            None,  # 可以从 event_chain.timestamp 计算时间延迟
            relationship_label
        )
        
        logger.info(
            f"创建事件链成功: {event_chain.source}({source_node_label}) -> "
            f"{event_chain.target}({target_node_label}), relation={relationship_label}"
        )
        
        return {
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "source_node_label": source_node_label,
            "target_node_label": target_node_label,
            "relationship_id": rel_id,
            "relationship_label": relationship_label
        }
    
    async def _get_or_create_event_node(self, event_description: str) -> tuple[str, str]:
        """获取或创建事件节点，返回 (node_id, node_label)"""
        # 首先尝试查找现有节点
        query = """
        MATCH (n)
        WHERE n.description = $description OR n.standard_term = $description
        RETURN n.id as node_id, labels(n) as labels
        LIMIT 1
        """
        
        result = await self.execute_query(
            query,
            {"description": event_description},
            fetch_all=False
        )
        
        if result and result.get("node_id"):
            labels = result.get("labels") or []
            return result["node_id"], (labels[0] if labels else "FireEvent")
        
        # 如果不存在，根据描述内容智能分类并创建新节点
        node_type, node_label = self._classify_event_type(event_description)
        node_id = str(uuid.uuid4())
        
        if node_label == "FireEvent":
            event_node = FireEventNode(
                id=node_id,
                event_type=node_type,
                description=event_description,
                standard_term=event_description,
                category="未分类",
                severity_level=5,
                frequency=1
            )
            created_id = await self.create_fire_event_node(event_node)
            return created_id, "FireEvent"
        elif node_label == "Hazard":
            hazard_node = HazardNode(
                id=node_id,
                description=event_description,
                risk_level="中",
                location="未知"
            )
            created_id = await self.create_hazard_node(hazard_node)
            return created_id, "Hazard"
        else:  # Consequence
            consequence_node = ConsequenceNode(
                id=node_id,
                description=event_description,
                impact_level="中",
                affected_area="未知"
            )
            created_id = await self.create_consequence_node(consequence_node)
            return created_id, "Consequence"
    
    def _determine_relationship_label(self, source_label: str, target_label: str) -> str:
        """根据源/目标节点类型确定关系类型，保证结构符合 隐患 -> 火灾事件 -> 后果"""
        if source_label == "Hazard" and target_label == "FireEvent":
            return "LEADS_TO"
        if source_label == "FireEvent" and target_label == "Consequence":
            return "RESULTS_IN"
        if source_label == "Hazard" and target_label == "Consequence":
            return "RESULTS_IN"
        return "CAUSES"
    
    def _classify_event_type(self, description: str) -> tuple[str, str]:
        """
        根据事件描述智能分类节点类型
        
        Returns:
            (event_type, node_label): 事件类型和节点标签
        """
        desc_lower = description.lower().strip()

        hazard_keywords = [
            "隐患", "老化", "破损", "故障", "缺陷", "不合格", "违规",
            "未检查", "未维护", "未及时", "缺乏", "不到位", "不规范",
            "超负荷", "过载", "短路", "漏电", "绝缘", "腐蚀", "锈蚀",
            "堆放", "堵塞", "占用", "私拉", "乱接", "改装", "失效",
            "损坏", "异常", "松动", "裸露", "未设置", "未安装", "未配备"
        ]

        fire_event_keywords = [
            "起火", "着火", "燃烧", "火灾", "火势", "明火", "火焰", "火星",
            "爆炸", "爆燃", "闪燃", "轰燃", "复燃", "阴燃",
            "烟雾", "浓烟", "烟气", "高温", "过热", "发热",
            "点燃", "引燃", "自燃", "电弧", "火花", "烟头"
        ]

        consequence_keywords = [
            "伤亡", "死亡", "受伤", "损失", "烧毁", "坍塌", "蔓延", "扩散",
            "波及", "影响", "污染", "中毒", "窒息", "财产损失", "经济损失",
            "人员伤亡", "群众", "居民", "停产", "停电", "破坏", "报废"
        ]

        if any(kw in desc_lower for kw in consequence_keywords):
            return ("后果", "Consequence")

        if any(kw in desc_lower for kw in fire_event_keywords):
            return ("过程", "FireEvent")

        if any(kw in desc_lower for kw in hazard_keywords):
            return ("隐患", "Hazard")

        # 带有明显结果语义的短语优先判为后果，避免“导致/造成/引起/发生”把前因误判成后果
        if desc_lower.startswith(("导致", "造成", "引起")):
            return ("后果", "Consequence")

        # 默认未知前因更适合放入隐患，而不是火灾事件，可减少导入后整图偏红
        return ("隐患", "Hazard")
    
    # ===== 查询操作 =====
    
    async def find_paths(
        self,
        start_node_id: str,
        end_node_id: Optional[str] = None,
        max_depth: int = 5,
        relationship_types: Optional[List[str]] = None
    ) -> List[Path]:
        """查找路径"""
        if relationship_types:
            rel_filter = "|".join(relationship_types)
            rel_pattern = f"[r:{rel_filter}*1..{max_depth}]"
        else:
            rel_pattern = f"[r*1..{max_depth}]"
        
        if end_node_id:
            # 查找特定起点到终点的路径
            query = f"""
            MATCH path = (start {{id: $start_id}})-{rel_pattern}->(end {{id: $end_id}})
            RETURN path
            LIMIT 10
            """
            parameters = {"start_id": start_node_id, "end_id": end_node_id}
        else:
            # 查找从起点出发的所有路径
            query = f"""
            MATCH path = (start {{id: $start_id}})-{rel_pattern}->(end)
            RETURN path
            LIMIT 20
            """
            parameters = {"start_id": start_node_id}
        
        results = await self.execute_query(query, parameters)
        
        paths = []
        for result in results:
            # 解析路径数据（简化版本）
            path_data = result["path"]
            # 这里需要解析 Neo4j 路径对象，转换为我们的 Path 模型
            # 暂时返回空列表，实际实现需要解析路径节点和关系
            pass
        
        return paths
    
    async def get_node_neighbors(
        self,
        node_id: str,
        direction: str = "OUTGOING",
        relationship_types: Optional[List[str]] = None
    ) -> List[Node]:
        """获取节点的邻居"""
        if relationship_types:
            rel_filter = "|".join(relationship_types)
            rel_pattern = f"[r:{rel_filter}]"
        else:
            rel_pattern = "[r]"
        
        if direction.upper() == "OUTGOING":
            pattern = f"(n {{id: $node_id}})-{rel_pattern}->(neighbor)"
        elif direction.upper() == "INCOMING":
            pattern = f"(n {{id: $node_id}})<-{rel_pattern}-(neighbor)"
        else:  # BOTH
            pattern = f"(n {{id: $node_id}})-{rel_pattern}-(neighbor)"
        
        query = f"""
        MATCH {pattern}
        RETURN neighbor, labels(neighbor) as labels
        """
        
        results = await self.execute_query(query, {"node_id": node_id})
        
        neighbors = []
        for result in results:
            node_data = result["neighbor"]
            labels = result["labels"]
            
            neighbor = Node(
                id=node_data["id"],
                labels=labels,
                properties=dict(node_data),
                created_at=datetime.fromisoformat(node_data.get("created_at", datetime.now().isoformat())),
                updated_at=datetime.fromisoformat(node_data.get("updated_at", datetime.now().isoformat()))
            )
            neighbors.append(neighbor)
        
        return neighbors
    
    # ===== 统计信息 =====
    
    async def get_graph_statistics(self) -> GraphStatistics:
        """获取图统计信息"""
        # 节点总数
        node_count_result = await self.execute_query(
            "MATCH (n) RETURN count(n) as count",
            fetch_all=False
        )
        node_count = node_count_result.get("count", 0)
        
        # 关系总数
        rel_count_result = await self.execute_query(
            "MATCH ()-[r]->() RETURN count(r) as count",
            fetch_all=False
        )
        relationship_count = rel_count_result.get("count", 0)
        
        # 节点类型分布
        node_type_results = await self.execute_query(
            "MATCH (n) RETURN labels(n) as labels, count(n) as count"
        )
        node_type_distribution = {}
        for result in node_type_results:
            labels = result["labels"]
            if labels:
                label = labels[0]  # 取第一个标签
                node_type_distribution[label] = result["count"]
        
        # 关系类型分布
        rel_type_results = await self.execute_query(
            "MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count"
        )
        relationship_type_distribution = {}
        for result in rel_type_results:
            relationship_type_distribution[result["rel_type"]] = result["count"]
        
        # 平均度数
        avg_degree = (relationship_count * 2) / node_count if node_count > 0 else 0
        
        return GraphStatistics(
            node_count=node_count,
            relationship_count=relationship_count,
            node_type_distribution=node_type_distribution,
            relationship_type_distribution=relationship_type_distribution,
            avg_degree=avg_degree,
            max_depth=5  # 默认值，可以通过实际查询计算
        )
    
    # ===== 批量操作 =====
    
    async def batch_create_nodes(self, nodes: List[NodeCreate]) -> List[str]:
        """批量创建节点"""
        node_ids = []
        
        async with await self.get_session() as session:
            async with session.begin_transaction() as tx:
                for node_data in nodes:
                    node_id = str(uuid.uuid4())
                    labels_str = ":".join(node_data.labels)
                    
                    properties = node_data.properties.copy()
                    properties.update({
                        "id": node_id,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    })
                    
                    query = f"""
                    CREATE (n:{labels_str})
                    SET n = $properties
                    RETURN n.id as node_id
                    """
                    
                    result = await tx.run(query, {"properties": properties})
                    record = await result.single()
                    node_ids.append(record["node_id"])
        
        logger.info(f"批量创建节点成功: {len(node_ids)} 个节点")
        return node_ids
    
    async def batch_create_relationships(self, relationships: List[RelationshipCreate]) -> List[str]:
        """批量创建关系"""
        rel_ids = []
        
        async with await self.get_session() as session:
            async with session.begin_transaction() as tx:
                for rel_data in relationships:
                    rel_id = str(uuid.uuid4())
                    
                    properties = rel_data.properties.copy()
                    properties.update({
                        "id": rel_id,
                        "created_at": datetime.now().isoformat()
                    })
                    
                    query = f"""
                    MATCH (start {{id: $start_node}})
                    MATCH (end {{id: $end_node}})
                    CREATE (start)-[r:{rel_data.type}]->(end)
                    SET r = $properties
                    RETURN r.id as rel_id
                    """
                    
                    result = await tx.run(query, {
                        "start_node": rel_data.start_node,
                        "end_node": rel_data.end_node,
                        "properties": properties
                    })
                    record = await result.single()
                    rel_ids.append(record["rel_id"])
        
        logger.info(f"批量创建关系成功: {len(rel_ids)} 个关系")
        return rel_ids


# 全局 Neo4j 管理器实例
neo4j_manager = Neo4jManager()