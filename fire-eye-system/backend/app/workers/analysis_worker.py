"""
文档分析后台工作器
处理文本分析任务，提取事件链和实体关系
"""

import logging
import asyncio
from typing import Dict, Any

from app.services.task_manager import task_manager, TaskType, TaskStatus, TaskResult
from app.services.extraction_service import extraction_service
from app.services.graph_service import graph_service
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


async def process_analyze_task(task_id: str, text: str, metadata: Dict[str, Any] = None) -> None:
    """
    处理文档分析任务
    
    Args:
        task_id: 任务 ID
        text: 要分析的文本内容
        metadata: 任务元数据
    """
    try:
        logger.info(f"Starting analysis task {task_id}")
        
        # 更新进度：开始处理
        await task_manager.update_task_progress(
            task_id=task_id,
            progress=10,
            status=TaskStatus.PROCESSING
        )
        
        # 步骤 1: 使用 LLM 提取事件链
        logger.info(f"Task {task_id}: Extracting event chains using LLM")
        
        # 调用 LLM 服务提取事件链
        event_chains_data = await llm_service.extract_event_chains(text)
        
        # Convert EventChainCreate objects to dicts
        event_chains_list = []
        for chain in event_chains_data:
            if hasattr(chain, 'model_dump'):
                event_chains_list.append(chain.model_dump())
            elif isinstance(chain, dict):
                event_chains_list.append(chain)
            else:
                logger.warning(f"Unexpected chain type: {type(chain)}")
        
        # 更新进度：提取完成
        await task_manager.update_task_progress(
            task_id=task_id,
            progress=50,
            status=TaskStatus.PROCESSING
        )
        
        # 步骤 2: 存储到图数据库
        logger.info(f"Task {task_id}: Storing to graph database")
        
        # 存储事件链
        node_count = 0
        relationship_count = 0
        
        for chain_data in event_chains_list:
            try:
                # 创建事件链
                await graph_service.create_event_chain(chain_data)
                node_count += 2  # source and target
                relationship_count += 1
            except Exception as e:
                logger.warning(f"Failed to store event chain: {e}")
        
        # 更新进度：存储完成
        await task_manager.update_task_progress(
            task_id=task_id,
            progress=90,
            status=TaskStatus.PROCESSING
        )
        
        # 步骤 3: 完成任务
        result = TaskResult(
            event_chains=event_chains_list,
            entities_count=node_count,
            relationships_count=relationship_count,
            document_id=metadata.get("document_id") if metadata else None
        )
        
        await task_manager.complete_task(task_id=task_id, result=result)
        logger.info(f"Task {task_id} completed successfully with {node_count} nodes and {relationship_count} relationships")
    
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)
        await task_manager.fail_task(task_id=task_id, error=str(e))
        stored_chains = []
        for chain in extraction_result.event_chains:
            try:
                # 将事件链存储到 Neo4j
                chain_dict = chain.model_dump() if hasattr(chain, 'model_dump') else chain
                stored_chain = await graph_service.store_event_chain(chain_dict)
                stored_chains.append(stored_chain)
            except Exception as e:
                logger.error(f"Task {task_id}: Failed to store event chain: {e}")
                # 继续处理其他事件链
        
        # 更新进度：存储完成
        await task_manager.update_task_progress(
            task_id=task_id,
            progress=90,
            status=TaskStatus.PROCESSING
        )
        
        # 步骤 3: 准备结果
        result = TaskResult(
            event_chains=stored_chains,
            entities_count=len(extraction_result.entities),
            relationships_count=len(extraction_result.relationships),
            message=f"成功分析文档，提取 {len(stored_chains)} 个事件链，{len(extraction_result.entities)} 个实体，{len(extraction_result.relationships)} 个关系"
        )
        
        # 完成任务
        await task_manager.complete_task(task_id=task_id, result=result)
        
        logger.info(f"Task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)
        
        # 标记任务失败
        await task_manager.fail_task(
            task_id=task_id,
            error=f"分析失败: {str(e)}"
        )


def start_analyze_task(task_id: str, text: str, metadata: Dict[str, Any] = None) -> asyncio.Task:
    """
    启动文档分析任务（非阻塞）
    
    Args:
        task_id: 任务 ID
        text: 要分析的文本内容
        metadata: 任务元数据
        
    Returns:
        asyncio.Task 对象
    """
    return asyncio.create_task(process_analyze_task(task_id, text, metadata))
