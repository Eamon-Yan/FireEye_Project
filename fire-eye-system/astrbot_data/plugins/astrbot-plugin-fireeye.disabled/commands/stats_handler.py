"""
统计命令处理器
处理 /火瞳统计 和 /ht统计 命令
"""

from loguru import logger
from api.client import APIClient
from utils.formatter import MessageFormatter


class StatsHandler:
    """统计命令处理器"""
    
    def __init__(
        self,
        api_client: APIClient,
        formatter: MessageFormatter
    ):
        """
        初始化统计处理器
        
        Args:
            api_client: API 客户端
            formatter: 消息格式化器
        """
        self.api_client = api_client
        self.formatter = formatter
        
        logger.info("StatsHandler initialized")
    
    async def handle(self, message, user_id: str, platform: str = "unknown"):
        """
        处理统计命令
        
        Args:
            message: 消息对象（根据 AstrBot API 调整）
            user_id: 用户 ID
            platform: 平台类型
            
        Returns:
            响应消息
        """
        try:
            # 提取统计类型参数
            stat_type = self._extract_stat_type(message)
            
            logger.info(f"Processing stats request from user {user_id}: type={stat_type}")
            
            # 调用 API 获取统计信息
            response = await self.api_client.get_stats(
                stat_type=stat_type,
                time_range="all"
            )
            
            # 格式化响应
            formatted_message = self.formatter.format_statistics(response)
            
            return formatted_message
            
        except Exception as e:
            logger.error(f"Error handling stats: {e}", exc_info=True)
            return self.formatter.format_error(f"获取统计信息失败: {str(e)}")
    
    def _extract_stat_type(self, message) -> str:
        """
        从消息中提取统计类型
        
        Args:
            message: 消息对象
            
        Returns:
            统计类型（如 "hazard", "consequence" 等）
        """
        # 这里需要根据 AstrBot 的实际消息格式进行调整
        if isinstance(message, str):
            text = message.strip()
            for prefix in ['/火瞳统计', '/ht统计']:
                if text.startswith(prefix):
                    text = text[len(prefix):].strip()
                    break
            
            # 映射中文类型到英文
            type_mapping = {
                '隐患': 'hazard',
                '后果': 'consequence',
                '事件': 'fire_event',
                '全部': 'all'
            }
            
            return type_mapping.get(text, 'all')
        
        # 如果是消息对象，提取文本内容
        if hasattr(message, 'text'):
            text = message.text.strip()
            for prefix in ['/火瞳统计', '/ht统计']:
                if text.startswith(prefix):
                    text = text[len(prefix):].strip()
                    break
            
            type_mapping = {
                '隐患': 'hazard',
                '后果': 'consequence',
                '事件': 'fire_event',
                '全部': 'all'
            }
            
            return type_mapping.get(text, 'all')
        
        return 'all'
