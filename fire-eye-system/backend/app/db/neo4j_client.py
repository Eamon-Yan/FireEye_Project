"""
Neo4j 数据库客户端
"""

import logging
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import ServiceUnavailable, AuthError

from app.core.config import settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Neo4j 数据库客户端"""
    
    def __init__(self):
        self.driver: Optional[AsyncDriver] = None
        self.uri = settings.NEO4J_URI
        self.username = settings.NEO4J_USERNAME
        self.password = settings.NEO4J_PASSWORD
        self.database = settings.NEO4J_DATABASE
    
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
            await self.verify_connectivity()
            logger.info("Neo4j 数据库连接成功")
            
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Neo4j 连接失败: {e}")
            raise
    
    async def disconnect(self) -> None:
        """关闭数据库连接"""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j 数据库连接已关闭")
    
    async def verify_connectivity(self) -> None:
        """验证数据库连接"""
        if not self.driver:
            raise RuntimeError("数据库驱动未初始化")
        
        try:
            await self.driver.verify_connectivity()
        except Exception as e:
            logger.error(f"Neo4j 连接验证失败: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """获取数据库会话上下文管理器"""
        if not self.driver:
            raise RuntimeError("数据库驱动未初始化")
        
        session = self.driver.session(database=self.database)
        try:
            yield session
        finally:
            await session.close()
    
    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """执行 Cypher 查询"""
        if parameters is None:
            parameters = {}
        
        db_name = database or self.database
        
        async with self.get_session() as session:
            try:
                result = await session.run(query, parameters, database=db_name)
                records = await result.data()
                return records
            except Exception as e:
                logger.error(f"查询执行失败: {query}, 错误: {e}")
                raise
    
    async def execute_write_transaction(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """执行写事务"""
        if parameters is None:
            parameters = {}
        
        async with self.get_session() as session:
            try:
                result = await session.execute_write(
                    self._execute_query_tx, query, parameters
                )
                return result
            except Exception as e:
                logger.error(f"写事务执行失败: {query}, 错误: {e}")
                raise
    
    async def execute_read_transaction(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """执行读事务"""
        if parameters is None:
            parameters = {}
        
        async with self.get_session() as session:
            try:
                result = await session.execute_read(
                    self._execute_query_tx, query, parameters
                )
                return result
            except Exception as e:
                logger.error(f"读事务执行失败: {query}, 错误: {e}")
                raise
    
    @staticmethod
    async def _execute_query_tx(tx, query: str, parameters: Dict[str, Any]):
        """事务执行器"""
        result = await tx.run(query, parameters)
        return await result.data()
    
    async def create_constraints_and_indexes(self) -> None:
        """创建约束和索引"""
        constraints_and_indexes = [
            # 节点唯一性约束
            "CREATE CONSTRAINT fire_event_id_unique IF NOT EXISTS FOR (n:FireEvent) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT hazard_id_unique IF NOT EXISTS FOR (n:Hazard) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT consequence_id_unique IF NOT EXISTS FOR (n:Consequence) REQUIRE n.id IS UNIQUE",
            
            # 关系唯一性约束
            "CREATE CONSTRAINT causal_relation_id_unique IF NOT EXISTS FOR ()-[r:CAUSES]-() REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT leads_to_relation_id_unique IF NOT EXISTS FOR ()-[r:LEADS_TO]-() REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT results_in_relation_id_unique IF NOT EXISTS FOR ()-[r:RESULTS_IN]-() REQUIRE r.id IS UNIQUE",
            
            # 性能索引
            "CREATE INDEX fire_event_type_index IF NOT EXISTS FOR (n:FireEvent) ON (n.event_type)",
            "CREATE INDEX fire_event_category_index IF NOT EXISTS FOR (n:FireEvent) ON (n.category)",
            "CREATE INDEX fire_event_severity_index IF NOT EXISTS FOR (n:FireEvent) ON (n.severity_level)",
            "CREATE INDEX fire_event_standard_term_index IF NOT EXISTS FOR (n:FireEvent) ON (n.standard_term)",
            "CREATE INDEX hazard_risk_level_index IF NOT EXISTS FOR (n:Hazard) ON (n.risk_level)",
            "CREATE INDEX consequence_impact_level_index IF NOT EXISTS FOR (n:Consequence) ON (n.impact_level)",
            
            # 全文搜索索引
            "CREATE FULLTEXT INDEX fire_event_description_fulltext IF NOT EXISTS FOR (n:FireEvent) ON EACH [n.description, n.standard_term]",
            "CREATE FULLTEXT INDEX hazard_description_fulltext IF NOT EXISTS FOR (n:Hazard) ON EACH [n.description]",
        ]
        
        for constraint_or_index in constraints_and_indexes:
            try:
                await self.execute_query(constraint_or_index)
                logger.info(f"成功创建约束/索引: {constraint_or_index}")
            except Exception as e:
                logger.warning(f"创建约束/索引失败 (可能已存在): {constraint_or_index}, 错误: {e}")


# 全局 Neo4j 客户端实例
neo4j_client = Neo4jClient()