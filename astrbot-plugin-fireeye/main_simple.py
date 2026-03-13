"""
Fire-Eye AstrBot Plugin - Simplified Version
火瞳系统 AstrBot 插件 - 简化版本
"""

from astrbot.core.star import Star, Context
from astrbot.core import logger


class FireEyePlugin(Star):
    """Fire-Eye 插件主类"""
    
    # 类属性（必须在类级别定义）
    name: str = "Fire-Eye"
    author: str = "FireEye Team"
    desc: str = "火瞳火灾调查知识图谱查询插件"
    version: str = "1.0.0"
    
    def __init__(self, context: Context, config: dict = None):
        """初始化插件"""
        super().__init__(context, config)
        logger.info(f"[Fire-Eye] Plugin initialized v{self.version}")
