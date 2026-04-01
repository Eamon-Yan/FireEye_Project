"""
消息格式化器
将 API 响应格式化为适合聊天平台显示的消息
"""

from typing import Dict, Any, List
from loguru import logger


class MessageFormatter:
    """消息格式化器"""
    
    def __init__(self, max_message_length: int = 2000):
        """
        初始化消息格式化器
        
        Args:
            max_message_length: 单条消息最大长度
        """
        self.max_message_length = max_message_length
        logger.info(f"MessageFormatter initialized: max_length={max_message_length}")
    
    def format_query_results(self, response: Dict[str, Any]) -> str:
        """
        格式化查询结果
        
        Args:
            response: API 响应数据
            
        Returns:
            格式化的消息文本
        """
        try:
            data = response.get('data', {})
            results = data.get('results', [])
            total_count = data.get('total_count', 0)
            
            if total_count == 0:
                return "❌ 未找到相关信息"
            
            message = f"🔍 查询结果（共 {total_count} 条）\n\n"
            
            # 显示前几条结果
            display_count = min(5, len(results))
            for i, result in enumerate(results[:display_count], 1):
                message += self._format_single_result(i, result)
                message += "\n"
            
            if total_count > display_count:
                message += f"\n... 还有 {total_count - display_count} 条结果"
            
            return self._truncate_message(message)
            
        except Exception as e:
            logger.error(f"Error formatting query results: {e}")
            return "❌ 格式化结果时出错"
    
    def _format_single_result(self, index: int, result: Dict[str, Any]) -> str:
        """格式化单个查询结果"""
        node_type = result.get('type', '未知')
        description = result.get('description', result.get('standard_term', '无描述'))
        
        formatted = f"{index}. 【{node_type}】{description}"
        
        # 添加额外信息
        if 'properties' in result:
            props = result['properties']
            if 'date' in props:
                formatted += f"\n   📅 日期: {props['date']}"
            if 'location' in props:
                formatted += f"\n   📍 地点: {props['location']}"
        
        return formatted
    
    def format_task_created(self, response: Dict[str, Any]) -> str:
        """
        格式化任务创建响应
        
        Args:
            response: API 响应数据
            
        Returns:
            格式化的消息文本
        """
        try:
            data = response.get('data', {})
            task_id = data.get('task_id', '未知')
            estimated_time = data.get('estimated_time', 60)
            
            message = (
                f"✅ 任务已创建\n\n"
                f"📋 任务 ID: {task_id}\n"
                f"⏱️ 预计时间: {estimated_time} 秒\n\n"
                f"正在处理中，请稍候..."
            )
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting task created: {e}")
            return "✅ 任务已创建，正在处理中..."
    
    def format_task_progress(self, progress: int) -> str:
        """
        格式化任务进度
        
        Args:
            progress: 进度百分比
            
        Returns:
            格式化的消息文本
        """
        bar_length = 20
        filled = int(bar_length * progress / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        return f"⏳ 处理进度: {bar} {progress}%"
    
    def format_task_completed(self, task_data: Dict[str, Any]) -> str:
        """
        格式化任务完成结果
        
        Args:
            task_data: 任务数据
            
        Returns:
            格式化的消息文本
        """
        try:
            result = task_data.get('result', {})
            
            if not result:
                return "✅ 任务完成"
            
            event_chains = result.get('event_chains', [])
            entities_count = result.get('entities_count', 0)
            relationships_count = result.get('relationships_count', 0)
            
            message = (
                f"✅ 分析完成\n\n"
                f"📊 提取结果:\n"
                f"  • 事件链: {len(event_chains)} 个\n"
                f"  • 实体: {entities_count} 个\n"
                f"  • 关系: {relationships_count} 个\n"
            )
            
            # 显示事件链摘要
            if event_chains:
                message += "\n🔗 事件链:\n"
                for i, chain in enumerate(event_chains[:3], 1):
                    chain_desc = chain.get('description', '未命名事件链')
                    message += f"  {i}. {chain_desc}\n"
                
                if len(event_chains) > 3:
                    message += f"  ... 还有 {len(event_chains) - 3} 个事件链\n"
            
            return self._truncate_message(message)
            
        except Exception as e:
            logger.error(f"Error formatting task completed: {e}")
            return "✅ 任务完成"
    
    def format_statistics(self, response: Dict[str, Any]) -> str:
        """
        格式化统计信息
        
        Args:
            response: API 响应数据
            
        Returns:
            格式化的消息文本
        """
        try:
            data = response.get('data', {})
            
            message = "📊 火瞳系统统计信息\n\n"
            
            # 基础统计
            if 'total_fire_events' in data:
                message += f"🔥 火灾事件: {data['total_fire_events']} 起\n"
            if 'total_hazards' in data:
                message += f"⚠️ 火灾隐患: {data['total_hazards']} 个\n"
            if 'total_consequences' in data:
                message += f"💥 火灾后果: {data['total_consequences']} 个\n"
            
            # 分布统计
            if 'hazard_distribution' in data:
                message += "\n📈 隐患分布:\n"
                distribution = data['hazard_distribution']
                for hazard_type, count in list(distribution.items())[:5]:
                    message += f"  • {hazard_type}: {count}\n"
            
            return self._truncate_message(message)
            
        except Exception as e:
            logger.error(f"Error formatting statistics: {e}")
            return "❌ 格式化统计信息时出错"
    
    def format_error(self, error_message: str) -> str:
        """
        格式化错误消息
        
        Args:
            error_message: 错误消息
            
        Returns:
            格式化的消息文本
        """
        return f"❌ 错误: {error_message}"
    
    def format_help(self) -> str:
        """
        格式化帮助信息
        
        Returns:
            帮助消息文本
        """
        help_text = """
🔥 火瞳系统 - 帮助信息

📖 可用命令:

1️⃣ 查询命令
   /火瞳查询 <查询内容>
   /ht查询 <查询内容>
   示例: /火瞳查询 3.21火灾事故

2️⃣ 上传文档
   /火瞳上传
   /ht上传
   然后发送文件（支持 PDF、DOCX、TXT）

3️⃣ 查看统计
   /火瞳统计 [类型]
   /ht统计 [类型]
   示例: /火瞳统计 隐患

4️⃣ 帮助信息
   /火瞳帮助
   /ht帮助

💡 提示:
• 支持多轮对话，可以连续提问
• 上传的文档会自动分析并存入知识图谱
• 查询支持自然语言，如"主要原因是什么"
        """.strip()
        
        return help_text
    
    def _truncate_message(self, message: str) -> str:
        """
        截断过长的消息
        
        Args:
            message: 原始消息
            
        Returns:
            截断后的消息
        """
        if len(message) <= self.max_message_length:
            return message
        
        truncated = message[:self.max_message_length - 50]
        truncated += "\n\n... (消息过长，已截断)"
        
        logger.warning(f"Message truncated: {len(message)} -> {len(truncated)}")
        return truncated
