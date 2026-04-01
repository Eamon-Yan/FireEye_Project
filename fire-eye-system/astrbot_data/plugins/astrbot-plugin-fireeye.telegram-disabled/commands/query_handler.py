"""
查询命令处理器
处理 /火瞳查询 和 /ht查询 命令
"""

from loguru import logger
from api.client import APIClient
from session.manager import SessionManager
from request_queue_module import RequestQueue, QueueFullError
from utils.formatter import MessageFormatter


class QueryHandler:
    """查询命令处理器"""
    
    def __init__(
        self,
        api_client: APIClient,
        session_manager: SessionManager,
        request_queue: RequestQueue,
        formatter: MessageFormatter
    ):
        """
        初始化查询处理器
        
        Args:
            api_client: API 客户端
            session_manager: 会话管理器
            request_queue: 请求队列
            formatter: 消息格式化器
        """
        self.api_client = api_client
        self.session_manager = session_manager
        self.request_queue = request_queue
        self.formatter = formatter
        
        logger.info("QueryHandler initialized")
    
    async def handle(self, message, user_id: str, platform: str = "unknown"):
        """
        处理查询命令
        
        Args:
            message: 消息对象（根据 AstrBot API 调整）
            user_id: 用户 ID
            platform: 平台类型
            
        Returns:
            响应消息
        """
        try:
            # 提取查询文本
            query_text = self._extract_query_text(message)
            
            if not query_text:
                return "❌ 请提供查询内容\n\n示例: /火瞳查询 3.21火灾事故"
            
            logger.info(f"Processing query from user {user_id}: {query_text}")
            
            # 获取或创建会话
            session_id = self.session_manager.get_session(user_id)
            if not session_id:
                session_id = self.session_manager.create_session(user_id, platform)
            
            # 将请求加入队列
            try:
                response = await self.request_queue.enqueue(
                    self._execute_query,
                    query_text,
                    session_id
                )
                
                # 格式化响应
                formatted_message = self.formatter.format_query_results(response)
                
                # 更新会话活动时间
                self.session_manager.update_activity(user_id)
                
                return formatted_message
                
            except QueueFullError as e:
                logger.warning(f"Queue full for user {user_id}")
                return self.formatter.format_error(
                    "系统繁忙，请稍后再试"
                )
            
        except Exception as e:
            logger.error(f"Error handling query: {e}", exc_info=True)
            return self.formatter.format_error(f"查询失败: {str(e)}")
    
    async def _execute_query(self, query_text: str, session_id: str):
        """
        执行查询请求
        
        Args:
            query_text: 查询文本
            session_id: 会话 ID
            
        Returns:
            API 响应
        """
        logger.debug(f"Executing query: {query_text} (session: {session_id})")
        
        response = await self.api_client.query(
            query=query_text,
            session_id=session_id
        )
        
        return response
    
    def _extract_query_text(self, message) -> str:
        """
        从消息中提取查询文本
        
        Args:
            message: 消息对象
            
        Returns:
            查询文本
        """
        # 这里需要根据 AstrBot 的实际消息格式进行调整
        # 示例实现：
        if isinstance(message, str):
            # 移除命令前缀
            text = message.strip()
            for prefix in ['/火瞳查询', '/ht查询']:
                if text.startswith(prefix):
                    text = text[len(prefix):].strip()
                    break
            return text
        
        # 如果是消息对象，提取文本内容
        if hasattr(message, 'text'):
            text = message.text.strip()
            for prefix in ['/火瞳查询', '/ht查询']:
                if text.startswith(prefix):
                    text = text[len(prefix):].strip()
                    break
            return text
        
        return ""
