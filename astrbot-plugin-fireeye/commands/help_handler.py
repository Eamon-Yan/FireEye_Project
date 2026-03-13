"""
帮助命令处理器
处理 /火瞳帮助 和 /ht帮助 命令
"""

from loguru import logger
from utils.formatter import MessageFormatter


class HelpHandler:
    """帮助命令处理器"""
    
    def __init__(self, formatter: MessageFormatter):
        """
        初始化帮助处理器
        
        Args:
            formatter: 消息格式化器
        """
        self.formatter = formatter
        
        logger.info("HelpHandler initialized")
    
    async def handle(self, message, user_id: str, platform: str = "unknown"):
        """
        处理帮助命令
        
        Args:
            message: 消息对象（根据 AstrBot API 调整）
            user_id: 用户 ID
            platform: 平台类型
            
        Returns:
            帮助消息
        """
        logger.info(f"Processing help request from user {user_id}")
        
        # 返回格式化的帮助信息
        return self.formatter.format_help()
