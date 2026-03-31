"""
Fire-Eye QQ Plugin - Minimal Version
最小化版本，用于测试基本功能
"""

from astrbot.api import star
from astrbot.api.event import AstrMessageEvent, filter, MessageEventResult
from loguru import logger


class Main(star.Star):
    """Fire-Eye QQ 插件 - 最小化版本"""
    
    def __init__(self, context: star.Context):
        """初始化插件"""
        self.context = context
        logger.info("[Fire-Eye QQ MINIMAL] Plugin initialized")
    
    # ==================== 测试命令 ====================
    
    @filter.command("火瞳帮助", alias={"ht帮助"})
    async def help_command(self, event: AstrMessageEvent):
        """帮助命令 - 测试版本"""
        logger.info("[Fire-Eye QQ MINIMAL] Help command triggered")
        event.set_result(MessageEventResult().message("✅ 帮助命令工作正常！"))
    
    @filter.command("火瞳查询", alias={"ht查询"})
    async def query_command(self, event: AstrMessageEvent):
        """查询命令 - 测试版本"""
        logger.info(f"[Fire-Eye QQ MINIMAL] Query command triggered: {event.message_str}")
        
        query_text = event.message_str.strip()
        
        # 移除命令前缀
        for prefix in ["/火瞳查询", "/ht查询", "火瞳查询", "ht查询"]:
            if query_text.startswith(prefix):
                query_text = query_text[len(prefix):].strip()
                break
        
        if not query_text:
            event.set_result(MessageEventResult().message("❌ 请提供查询内容"))
            return
        
        event.set_result(MessageEventResult().message(f"✅ 查询命令工作正常！\n查询内容: {query_text}"))
    
    @filter.command("火瞳统计", alias={"ht统计"})
    async def stats_command(self, event: AstrMessageEvent):
        """统计命令 - 测试版本"""
        logger.info("[Fire-Eye QQ MINIMAL] Stats command triggered")
        event.set_result(MessageEventResult().message("✅ 统计命令工作正常！"))
