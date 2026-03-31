"""
消息格式化器
将 API 响应格式化为 QQ 消息
"""

from typing import Dict, Any, List
from loguru import logger


class MessageFormatter:
    """消息格式化器"""
    
    def __init__(self, max_message_length: int = 4096, platform: str = "qq"):
        """
        初始化格式化器
        
        Args:
            max_message_length: 最大消息长度
            platform: 平台类型
        """
        self.max_message_length = max_message_length
        self.platform = platform
        
        logger.info(f"[Fire-Eye QQ] MessageFormatter initialized: platform={platform}, max_length={max_message_length}")
    
    def format_query_results(self, response: Dict[str, Any]) -> str:
        """
        格式化查询结果
        
        Args:
            response: API 响应
            
        Returns:
            格式化的消息
        """
        try:
            if response.get("status") != "success":
                error_msg = response.get("detail", "未知错误")
                return f"❌ 查询失败: {error_msg}"
            
            data = response.get("data", {})
            results = data.get("results", [])
            
            if not results:
                return "🔍 未找到相关信息"
            
            message = f"🔍 查询结果 ({len(results)} 条)\n\n"
            
            for i, item in enumerate(results[:10], 1):  # 最多显示10条
                node_type = item.get("type", "Unknown")
                name = item.get("name", item.get("id", ""))
                desc = item.get("description", "")
                
                message += f"{i}. [{node_type}] {name}\n"
                
                if desc:
                    # 截断过长的描述
                    if len(desc) > 100:
                        message += f"   {desc[:100]}...\n"
                    else:
                        message += f"   {desc}\n"
                
                # 显示相关节点
                related = item.get("related_nodes", [])
                if related:
                    for rel in related[:2]:  # 最多显示2个相关节点
                        rel_type = rel.get("type", "")
                        rel_name = rel.get("name", "")
                        relation = rel.get("relation", "")
                        confidence = rel.get("confidence", 0)
                        
                        message += f"   └─ {relation} → [{rel_type}] {rel_name} ({confidence:.0%})\n"
                
                message += "\n"
            
            if len(results) > 10:
                message += f"... 还有 {len(results) - 10} 条结果\n"
            
            # 检查消息长度
            if len(message) > self.max_message_length:
                message = message[:self.max_message_length - 20] + "\n... (消息过长，已截断)"
            
            return message
            
        except Exception as e:
            logger.error(f"[Fire-Eye QQ] Error formatting query results: {e}")
            return f"❌ 格式化结果失败: {str(e)}"
    
    def format_statistics(self, response: Dict[str, Any]) -> str:
        """
        格式化统计信息
        
        Args:
            response: API 响应
            
        Returns:
            格式化的消息
        """
        try:
            if response.get("status") != "success":
                error_msg = response.get("detail", "未知错误")
                return f"❌ 获取统计信息失败: {error_msg}"
            
            data = response.get("data", {})
            
            message = "📊 火瞳系统统计信息\n\n"
            
            # 基本统计
            message += "📈 数据概览:\n"
            message += f"• 事件总数: {data.get('total_events', 0)}\n"
            message += f"• 实体总数: {data.get('total_entities', 0)}\n"
            message += f"• 关系总数: {data.get('total_relationships', 0)}\n"
            message += f"• 文档总数: {data.get('total_documents', 0)}\n\n"
            
            # 节点类型统计
            node_types = data.get('node_types', {})
            if node_types:
                message += "📋 节点类型分布:\n"
                for node_type, count in sorted(node_types.items(), key=lambda x: x[1], reverse=True):
                    message += f"• {node_type}: {count}\n"
                message += "\n"
            
            # 关系类型统计
            rel_types = data.get('relationship_types', {})
            if rel_types:
                message += "🔗 关系类型分布:\n"
                for rel_type, count in sorted(rel_types.items(), key=lambda x: x[1], reverse=True):
                    message += f"• {rel_type}: {count}\n"
            
            # 检查消息长度
            if len(message) > self.max_message_length:
                message = message[:self.max_message_length - 20] + "\n... (消息过长，已截断)"
            
            return message
            
        except Exception as e:
            logger.error(f"[Fire-Eye QQ] Error formatting statistics: {e}")
            return f"❌ 格式化统计信息失败: {str(e)}"
    
    def format_error(self, error_msg: str) -> str:
        """
        格式化错误消息
        
        Args:
            error_msg: 错误信息
            
        Returns:
            格式化的错误消息
        """
        return f"❌ {error_msg}"
    
    def format_help(self) -> str:
        """
        格式化帮助信息
        
        Returns:
            帮助消息
        """
        help_text = """🔥 火瞳系统 - 帮助信息

📖 可用命令:

1️⃣ 查询命令
   /火瞳查询 <查询内容>
   /ht查询 <查询内容>
   示例: /火瞳查询 火灾

2️⃣ 统计命令
   /火瞳统计
   /ht统计
   查看系统统计信息

3️⃣ 帮助命令
   /火瞳帮助
   /ht帮助
   显示此帮助信息

💡 提示:
- 使用 /ht 作为 /火瞳 的简写
- 查询支持关键词搜索
- 系统会自动记录对话上下文

📞 需要帮助？请联系系统管理员"""
        
        return help_text
    
    def split_message(self, message: str) -> List[str]:
        """
        将长消息分割成多个短消息
        
        Args:
            message: 原始消息
            
        Returns:
            消息列表
        """
        if len(message) <= self.max_message_length:
            return [message]
        
        messages = []
        current_message = ""
        
        for line in message.split('\n'):
            if len(current_message) + len(line) + 1 > self.max_message_length:
                if current_message:
                    messages.append(current_message)
                current_message = line + "\n"
            else:
                current_message += line + "\n"
        
        if current_message:
            messages.append(current_message)
        
        return messages
