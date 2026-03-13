"""
图数据库 API 端点
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status

from app.db.dependencies import GraphServiceDep
from app.services.graph_service import GraphService
from app.schemas import (
    BaseResponse,
    ResponseStatus,
    FireEventNode,
    HazardNode,
    ConsequenceNode,
    EventChainCreate,
    NodeCreate,
    RelationshipCreate,
    GraphStatistics,
    QueryResult,
    PathFindingQuery,
    Node,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=BaseResponse)
async def graph_health_check(
    graph_service: GraphService = GraphServiceDep
):
    """图数据库健康检查"""
    try:
        is_healthy = await graph_service.health_check()
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS if is_healthy else ResponseStatus.ERROR,
            message="图数据库连接正常" if is_healthy else "图数据库连接异常",
            data={"healthy": is_healthy}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"图数据库健康检查失败: {str(e)}"
        )


@router.post("/nodes/fire-events", response_model=BaseResponse)
async def create_fire_event(
    event: FireEventNode,
    graph_service: GraphService = GraphServiceDep
):
    """创建火灾事件节点"""
    try:
        node_id = await graph_service.create_fire_event(event)
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="火灾事件节点创建成功",
            data={"node_id": node_id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建火灾事件节点失败: {str(e)}"
        )


@router.post("/nodes/hazards", response_model=BaseResponse)
async def create_hazard(
    hazard: HazardNode,
    graph_service: GraphService = GraphServiceDep
):
    """创建隐患节点"""
    try:
        node_id = await graph_service.create_hazard(hazard)
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="隐患节点创建成功",
            data={"node_id": node_id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建隐患节点失败: {str(e)}"
        )


@router.post("/nodes/consequences", response_model=BaseResponse)
async def create_consequence(
    consequence: ConsequenceNode,
    graph_service: GraphService = GraphServiceDep
):
    """创建后果节点"""
    try:
        node_id = await graph_service.create_consequence(consequence)
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="后果节点创建成功",
            data={"node_id": node_id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建后果节点失败: {str(e)}"
        )


@router.get("/nodes/{node_id}", response_model=BaseResponse)
async def get_node(
    node_id: str,
    graph_service: GraphService = GraphServiceDep
):
    """获取节点信息"""
    try:
        node = await graph_service.get_node(node_id)
        
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"节点不存在: {node_id}"
            )
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="获取节点成功",
            data=node.model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取节点失败: {str(e)}"
        )


@router.put("/nodes/{node_id}", response_model=BaseResponse)
async def update_node(
    node_id: str,
    properties: Dict[str, Any],
    graph_service: GraphService = GraphServiceDep
):
    """更新节点属性"""
    try:
        success = await graph_service.update_node(node_id, properties)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"节点不存在: {node_id}"
            )
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="节点更新成功",
            data={"node_id": node_id, "updated": True}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"更新节点失败: {str(e)}"
        )


@router.delete("/nodes/{node_id}", response_model=BaseResponse)
async def delete_node(
    node_id: str,
    graph_service: GraphService = GraphServiceDep
):
    """删除节点"""
    try:
        success = await graph_service.delete_node(node_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"节点不存在: {node_id}"
            )
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="节点删除成功",
            data={"node_id": node_id, "deleted": True}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"删除节点失败: {str(e)}"
        )


@router.post("/relationships", response_model=BaseResponse)
async def create_relationship(
    relationship: RelationshipCreate,
    graph_service: GraphService = GraphServiceDep
):
    """创建关系"""
    try:
        rel_id = await graph_service.create_relationship(relationship)
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="关系创建成功",
            data={"relationship_id": rel_id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建关系失败: {str(e)}"
        )


@router.post("/event-chains", response_model=BaseResponse)
async def create_event_chain(
    event_chain: EventChainCreate,
    graph_service: GraphService = GraphServiceDep
):
    """创建事件链"""
    try:
        result = await graph_service.create_event_chain(event_chain)
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="事件链创建成功",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建事件链失败: {str(e)}"
        )


@router.post("/event-chains/batch", response_model=BaseResponse)
async def batch_create_event_chains(
    event_chains: List[EventChainCreate],
    graph_service: GraphService = GraphServiceDep
):
    """批量创建事件链"""
    try:
        results = await graph_service.batch_create_event_chains(event_chains)
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"批量创建事件链成功: {len(results)}/{len(event_chains)}",
            data={
                "results": results,
                "success_count": len(results),
                "total_count": len(event_chains)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"批量创建事件链失败: {str(e)}"
        )


@router.get("/query", response_model=BaseResponse)
async def query_graph_data(
    node_types: Optional[str] = None,
    search_text: Optional[str] = None,
    limit: int = 100,
    include_relationships: bool = True,
    graph_service: GraphService = GraphServiceDep
):
    """
    查询图数据 - 为前端提供统一的数据接口
    
    参数:
    - node_types: 节点类型过滤，逗号分隔 (如: "FireEvent,Hazard")
    - search_text: 搜索文本，在节点描述中查找
    - limit: 返回结果数量限制 (最大100)
    - include_relationships: 是否包含关系数据
    """
    try:
        # 限制查询数量，防止过载
        limit = min(limit, 100)
        
        # 构建返回给前端的数据结构
        result_data = {
            "nodes": [],
            "links": []
        }
        
        # 使用简化的查询方式
        # 直接使用neo4j_manager而不是graph_service
        from app.db.neo4j_manager import neo4j_manager
        
        # 构建节点查询
        if search_text and search_text.strip():
            node_query = """
                MATCH (n)
                WHERE n.description CONTAINS $search_text 
                   OR n.standard_term CONTAINS $search_text
                RETURN n, labels(n) as node_labels
                LIMIT $limit
            """
            params = {"search_text": search_text.strip(), "limit": limit}
        else:
            node_query = """
                MATCH (n)
                RETURN n, labels(n) as node_labels
                LIMIT $limit
            """
            params = {"limit": limit}
        
        # 执行查询
        node_records = await neo4j_manager.execute_query(node_query, params)
        
        # 处理节点数据
        node_ids = []
        for record in node_records:
            try:
                node_data = record.get("n", {})
                node_labels = record.get("node_labels", [])
                
                node_id = node_data.get("id", "unknown")
                node_type = node_labels[0] if node_labels else "Unknown"
                
                # 转换Neo4j特殊类型为Python原生类型
                properties = {}
                for key, value in node_data.items():
                    if hasattr(value, 'iso_format'):  # Neo4j DateTime
                        properties[key] = value.iso_format()
                    elif hasattr(value, '__class__') and 'neo4j' in str(value.__class__):
                        properties[key] = str(value)
                    else:
                        properties[key] = value
                
                frontend_node = {
                    "id": node_id,
                    "type": node_type,
                    "description": node_data.get("description", node_data.get("standard_term", node_id)),
                    "properties": properties
                }
                
                result_data["nodes"].append(frontend_node)
                node_ids.append(node_id)
                
            except Exception as e:
                logger.warning(f"处理节点失败: {e}")
                continue
        
        # 查询关系
        if include_relationships and node_ids:
            try:
                rel_query = """
                    MATCH (a)-[r]->(b)
                    WHERE a.id IN $node_ids AND b.id IN $node_ids
                    RETURN type(r) as rel_type, a.id as source_id, b.id as target_id, r.confidence as confidence
                    LIMIT $rel_limit
                """
                
                rel_params = {
                    "node_ids": node_ids,
                    "rel_limit": min(len(node_ids) * 10, 500)
                }
                
                rel_records = await neo4j_manager.execute_query(rel_query, rel_params)
                
                for record in rel_records:
                    try:
                        frontend_link = {
                            "source": record.get("source_id"),
                            "target": record.get("target_id"),
                            "relation": record.get("rel_type", "RELATED"),
                            "confidence": record.get("confidence", 1.0)
                        }
                        
                        result_data["links"].append(frontend_link)
                        
                    except Exception as e:
                        logger.warning(f"处理关系失败: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"查询关系失败: {e}")
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"查询成功，返回 {len(result_data['nodes'])} 个节点，{len(result_data['links'])} 个关系",
            data=result_data
        )
        
    except Exception as e:
        logger.error(f"图数据查询失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # 返回空结构而不是500错误
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="查询完成，未找到匹配数据",
            data={"nodes": [], "links": []}
        )


@router.post("/cypher", response_model=BaseResponse)
async def execute_cypher_query(
    query: str,
    parameters: Optional[Dict[str, Any]] = None,
    graph_service: GraphService = GraphServiceDep
):
    """执行 Cypher 查询"""
    try:
        result = await graph_service.execute_cypher_query(query, parameters)
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="查询执行成功",
            data=result.model_dump()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"查询执行失败: {str(e)}"
        )


@router.get("/export", response_model=BaseResponse)
async def export_graph_data(
    format: str = "json",
    node_types: Optional[str] = None,
    limit: int = 1000,
    graph_service: GraphService = GraphServiceDep
):
    """
    导出图数据
    
    参数:
    - format: 导出格式 (json, cypher)
    - node_types: 节点类型过滤
    - limit: 导出数量限制
    """
    try:
        node_type_list = node_types.split(",") if node_types else None
        
        # 获取节点数据
        nodes = await graph_service.search_nodes_by_description(
            search_text="",
            node_types=node_type_list,
            limit=limit
        )
        
        if format.lower() == "json":
            # JSON格式导出
            export_data = {
                "nodes": [
                    {
                        "id": node.id,
                        "type": node.type,
                        "properties": node.properties
                    } for node in nodes
                ],
                "relationships": [],  # TODO: 实现关系导出
                "metadata": {
                    "export_time": datetime.now().isoformat(),
                    "node_count": len(nodes),
                    "format": "json"
                }
            }
        else:
            # 其他格式暂不支持
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的导出格式: {format}"
            )
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"导出成功，包含 {len(nodes)} 个节点",
            data=export_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出图数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出图数据失败: {str(e)}"
        )


@router.get("/search/nodes", response_model=BaseResponse)
async def search_nodes(
    q: str,
    node_types: Optional[str] = None,
    limit: int = 20,
    graph_service: GraphService = GraphServiceDep
):
    """搜索节点"""
    try:
        node_type_list = node_types.split(",") if node_types else None
        
        nodes = await graph_service.search_nodes_by_description(
            search_text=q,
            node_types=node_type_list,
            limit=limit
        )
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"搜索到 {len(nodes)} 个节点",
            data={
                "nodes": [node.model_dump() for node in nodes],
                "count": len(nodes)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"搜索节点失败: {str(e)}"
        )


@router.get("/nodes/{node_id}/neighbors", response_model=BaseResponse)
async def get_node_neighbors(
    node_id: str,
    direction: str = "OUTGOING",
    relationship_types: Optional[str] = None,
    graph_service: GraphService = GraphServiceDep
):
    """获取节点邻居"""
    try:
        rel_types = relationship_types.split(",") if relationship_types else None
        
        neighbors = await graph_service.get_node_neighbors(
            node_id=node_id,
            direction=direction,
            relationship_types=rel_types
        )
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"获取到 {len(neighbors)} 个邻居节点",
            data={
                "neighbors": [node.model_dump() for node in neighbors],
                "count": len(neighbors)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"获取邻居节点失败: {str(e)}"
        )


@router.get("/statistics", response_model=BaseResponse)
async def get_graph_statistics(
    graph_service: GraphService = GraphServiceDep
):
    """获取图统计信息"""
    try:
        stats = await graph_service.get_statistics()
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="获取统计信息成功",
            data=stats.model_dump()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )


@router.get("/export/subgraph", response_model=BaseResponse)
async def export_subgraph(
    node_ids: str,
    include_relationships: bool = True,
    graph_service: GraphService = GraphServiceDep
):
    """导出子图"""
    try:
        node_id_list = node_ids.split(",")
        
        subgraph = await graph_service.export_subgraph(
            node_ids=node_id_list,
            include_relationships=include_relationships
        )
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="子图导出成功",
            data=subgraph
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"导出子图失败: {str(e)}"
        )


@router.get("/search", response_model=BaseResponse)
async def search_graph_data(
    q: Optional[str] = None,
    node_types: Optional[str] = None,
    limit: int = 100,
    include_relationships: bool = True,
    graph_service: GraphService = GraphServiceDep
):
    """
    搜索图数据 - 兼容性端点
    
    参数:
    - q: 搜索查询文本
    - node_types: 节点类型过滤
    - limit: 返回结果数量限制
    - include_relationships: 是否包含关系数据
    """
    # 直接调用query_graph_data函数
    return await query_graph_data(
        node_types=node_types,
        search_text=q,
        limit=limit,
        include_relationships=include_relationships,
        graph_service=graph_service
    )