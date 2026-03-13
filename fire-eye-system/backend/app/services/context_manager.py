"""
上下文管理服务
用于解析多轮对话中的上下文引用
"""

import logging
from typing import Optional, List, Dict, Any

from app.services.session_service import session_service, SessionData
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class ContextManager:
    """上下文管理器"""
    
    def __init__(self):
        self.session_service = session_service
        self.llm_service = llm_service
    
    async def resolve_reference(
        self,
        session_id: str,
        query: str
    ) -> str:
        """
        解析查询中的上下文引用
        
        例如:
        - 上一轮: "查询3.21火灾事故" → 结果: [Event A, Event B, ...]
        - 当前轮: "主要原因是什么？"
        - 解析后: "3.21火灾事故的主要原因是什么？"
        
        Args:
            session_id: 会话 ID
            query: 用户查询
            
        Returns:
            解析后的查询（如果无需解析则返回原查询）
        """
        try:
            # 获取会话数据
            session_data = await self.session_service.get_session(session_id)
            if not session_data:
                logger.debug(f"No session found for {session_id}, returning original query")
                return query
            
            # 检查是否有对话历史
            if not session_data.conversation_history:
                logger.debug("No conversation history, returning original query")
                return query
            
            # 检查查询是否包含可能的引用词
            reference_keywords = ["它", "这个", "那个", "主要", "原因", "结果", "后果"]
            has_reference = any(keyword in query for keyword in reference_keywords)
            
            if not has_reference:
                logger.debug("No reference keywords detected, returning original query")
                return query
            
            # 获取最近的对话轮次
            last_turn = session_data.conversation_history[-1]
            
            # 如果没有查询结果，无法解析引用
            if not last_turn.query_results:
                logger.debug("No query results in last turn, returning original query")
                return query
            
            # 使用 LLM 解析上下文引用
            try:
                resolved_query = await self._resolve_with_llm(
                    query=query,
                    last_query=last_turn.user_message,
                    last_results=last_turn.query_results
                )
                
                logger.info(f"Resolved query: '{query}' -> '{resolved_query}'")
                return resolved_query
                
            except Exception as llm_error:
                logger.warning(f"LLM resolution failed: {llm_error}, using fallback")
                # 降级方案：简单拼接
                return await self._resolve_with_fallback(query, last_turn)
            
        except Exception as e:
            logger.error(f"Failed to resolve reference: {e}")
            # 出错时返回原查询
            return query
    
    async def _resolve_with_llm(
        self,
        query: str,
        last_query: str,
        last_results: List[Dict[str, Any]]
    ) -> str:
        """
        使用 LLM 解析上下文引用
        
        Args:
            query: 当前查询
            last_query: 上一轮查询
            last_results: 上一轮查询结果
            
        Returns:
            解析后的查询
        """
        # 构建提示词
        context_summary = self._summarize_results(last_results)
        
        prompt = f"""你是一个对话上下文解析助手。用户在进行多轮对话，你需要根据上下文将当前查询补充完整。

上一轮查询: {last_query}
上一轮结果摘要: {context_summary}

当前查询: {query}

请将当前查询补充完整，使其包含必要的上下文信息。如果当前查询已经完整，直接返回原查询。
只返回补充后的查询文本，不要添加任何解释。

补充后的查询:"""
        
        # 调用 LLM
        response = await self.llm_service.generate_text(
            prompt=prompt,
            max_tokens=200,
            temperature=0.3
        )
        
        # 清理响应
        resolved_query = response.strip()
        
        # 如果 LLM 返回的查询太短或太长，使用原查询
        if len(resolved_query) < 2 or len(resolved_query) > 500:
            return query
        
        return resolved_query
    
    async def _resolve_with_fallback(
        self,
        query: str,
        last_turn
    ) -> str:
        """
        降级方案：简单的上下文拼接
        
        Args:
            query: 当前查询
            last_turn: 上一轮对话
            
        Returns:
            拼接后的查询
        """
        # 提取上一轮查询的主题
        last_query = last_turn.user_message
        
        # 简单拼接
        if "原因" in query or "后果" in query or "结果" in query:
            return f"{last_query}的{query}"
        else:
            return query
    
    def _summarize_results(self, results: List[Dict[str, Any]]) -> str:
        """
        总结查询结果
        
        Args:
            results: 查询结果列表
            
        Returns:
            结果摘要
        """
        if not results:
            return "无结果"
        
        # 提取节点描述
        descriptions = []
        for result in results[:3]:  # 只取前3个结果
            if isinstance(result, dict):
                desc = result.get("description") or result.get("standard_term") or "未知"
                descriptions.append(desc)
        
        if descriptions:
            return "、".join(descriptions)
        else:
            return f"共{len(results)}个结果"


# 创建全局实例
context_manager = ContextManager()
