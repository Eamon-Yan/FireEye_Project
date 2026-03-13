"""
上传命令处理器
处理 /火瞳上传 命令
"""

import asyncio
from pathlib import Path
from astrbot.core import logger
from astrbot.api.event import MessageEventResult


class UploadHandler:
    """上传命令处理器"""
    
    def __init__(self, api_client, file_handler, task_poller, session_manager):
        """
        初始化上传处理器
        
        Args:
            api_client: API 客户端
            file_handler: 文件处理器
            task_poller: 任务轮询器
            session_manager: 会话管理器
        """
        self.api_client = api_client
        self.file_handler = file_handler
        self.task_poller = task_poller
        self.session_manager = session_manager
        
        logger.info("[UploadHandler] Initialized")
    
    async def handle(self, event, user_id: str):
        """
        处理上传命令
        
        Args:
            event: 消息事件
            user_id: 用户 ID
            
        Returns:
            响应消息
        """
        try:
            # 调试：打印事件对象的所有属性
            logger.info(f"[UploadHandler] Event type: {type(event)}")
            logger.info(f"[UploadHandler] Event attributes: {dir(event)}")
            
            # 尝试打印更多信息
            if hasattr(event, '__dict__'):
                logger.info(f"[UploadHandler] Event dict keys: {list(event.__dict__.keys())}")
            
            # 检查 message_obj
            if hasattr(event, 'message_obj') and event.message_obj:
                logger.info(f"[UploadHandler] message_obj found!")
                logger.info(f"[UploadHandler] message_obj type: {type(event.message_obj)}")
                logger.info(f"[UploadHandler] message_obj attributes: {dir(event.message_obj)}")
                if hasattr(event.message_obj, '__dict__'):
                    logger.info(f"[UploadHandler] message_obj dict keys: {list(event.message_obj.__dict__.keys())}")
                if hasattr(event.message_obj, 'chain'):
                    logger.info(f"[UploadHandler] message_obj.chain exists!")
                    logger.info(f"[UploadHandler] message_obj.chain type: {type(event.message_obj.chain)}")
                    logger.info(f"[UploadHandler] message_obj.chain length: {len(event.message_obj.chain)}")
                    for i, item in enumerate(event.message_obj.chain):
                        logger.info(f"[UploadHandler] chain[{i}] type: {type(item)}")
                        if hasattr(item, '__dict__'):
                            logger.info(f"[UploadHandler] chain[{i}] dict: {item.__dict__}")
            else:
                logger.info(f"[UploadHandler] No message_obj found")
            
            # 检查是否有文件附件 - 从 message_obj.chain 中查找
            has_attachments = False
            attachment = None
            
            # 首先从 message_obj.chain 中查找文件组件
            if hasattr(event, 'message_obj') and hasattr(event.message_obj, 'chain'):
                logger.info(f"[UploadHandler] Checking message_obj.chain")
                for i, component in enumerate(event.message_obj.chain):
                    component_type = type(component).__name__
                    logger.info(f"[UploadHandler] chain[{i}] type: {component_type}")
                    
                    # 检查是否是文件组件
                    if 'File' in component_type or 'Document' in component_type:
                        has_attachments = True
                        attachment = component
                        logger.info(f"[UploadHandler] File component found: {component_type}")
                        break
            
            # 如果没有找到，尝试其他方式
            if not has_attachments:
                if hasattr(event, 'attachments') and event.attachments:
                    has_attachments = True
                    attachment = event.attachments[0]
                    logger.info(f"[UploadHandler] Found attachments via event.attachments")
                elif hasattr(event, 'message') and hasattr(event.message, 'attachments') and event.message.attachments:
                    has_attachments = True
                    attachment = event.message.attachments[0]
                    logger.info(f"[UploadHandler] Found attachments via event.message.attachments")
                elif hasattr(event, 'message') and hasattr(event.message, 'file'):
                    has_attachments = True
                    attachment = event.message.file
                    logger.info(f"[UploadHandler] Found attachments via event.message.file")
            
            logger.info(f"[UploadHandler] has_attachments: {has_attachments}")
            
            if not has_attachments:
                return self._get_upload_instructions()
            
            # 检查是否是文件
            file_url = None
            filename = None
            
            # 尝试获取文件信息 - 支持多种属性名
            if hasattr(attachment, 'url'):
                file_url = attachment.url
            elif hasattr(attachment, 'file_url'):
                file_url = attachment.file_url
            elif hasattr(attachment, 'path'):
                file_url = attachment.path
                
            if hasattr(attachment, 'filename'):
                filename = attachment.filename
            elif hasattr(attachment, 'name'):
                filename = attachment.name
            elif hasattr(attachment, 'file_name'):
                filename = attachment.file_name
            
            logger.info(f"[UploadHandler] file_url: {file_url}, filename: {filename}")
            
            if not file_url or not filename:
                return "❌ 无法识别的文件格式\n\n" + self._get_upload_instructions()
            
            logger.info(f"[UploadHandler] Processing file: {filename} from {user_id}")
            
            # 验证文件类型
            valid, msg = self.file_handler.validate_file_type(filename)
            if not valid:
                return f"❌ {msg}"
            
            # 发送处理中消息
            await event.reply("📤 正在下载文件...")
            
            # 下载文件
            success, msg, file_path = await self.file_handler.download_from_url(file_url, filename)
            if not success:
                return f"❌ {msg}"
            
            # 发送上传中消息
            await event.reply("📤 正在上传到服务器...")
            
            # 获取会话 ID
            session_id = self.session_manager.get_or_create_session(user_id)
            
            # 上传文件
            success, msg, response = await self.file_handler.upload_to_backend(
                file_path,
                self.api_client.api_url,
                self.api_client.api_key,
                session_id
            )
            
            # 清理临时文件
            self.file_handler.cleanup_file(file_path)
            
            if not success:
                return f"❌ {msg}"
            
            # 获取任务 ID
            data = response.get("data", {})
            task_id = data.get("task_id")
            
            if not task_id:
                return "❌ 服务器未返回任务ID"
            
            # 发送分析中消息
            await event.reply(f"✅ 文件上传成功！\n\n🔄 正在分析文档...\n任务ID: {task_id}\n\n请稍候，这可能需要30-60秒...")
            
            # 开始轮询任务状态
            await self._poll_and_notify(event, task_id)
            
            return None  # 已经通过轮询发送了结果
            
        except Exception as e:
            logger.error(f"[UploadHandler] Error: {e}", exc_info=True)
            return f"❌ 上传失败: {str(e)}"
    
    async def _poll_and_notify(self, event, task_id: str):
        """
        轮询任务状态并通知用户
        
        Args:
            event: 消息事件
            task_id: 任务 ID
        """
        async def on_complete(result):
            """任务完成回调"""
            try:
                # 格式化结果
                message = self._format_result(result)
                await event.reply(message)
            except Exception as e:
                logger.error(f"[UploadHandler] Error in on_complete: {e}")
                await event.reply(f"❌ 结果格式化失败: {str(e)}")
        
        async def on_failed(error):
            """任务失败回调"""
            await event.reply(f"❌ 分析失败\n\n{error}")
        
        async def on_progress(progress, estimated_time):
            """进度更新回调（可选）"""
            if progress % 25 == 0:  # 每25%更新一次
                time_str = f"预计剩余 {estimated_time}秒" if estimated_time else ""
                await event.reply(f"🔄 分析进度: {progress}% {time_str}")
        
        # 开始轮询
        await self.task_poller.poll_task(
            task_id,
            on_complete=on_complete,
            on_failed=on_failed,
            on_progress=on_progress
        )
    
    def _format_result(self, result: dict) -> str:
        """
        格式化分析结果
        
        Args:
            result: 分析结果
            
        Returns:
            格式化的消息
        """
        try:
            event_chains = result.get("event_chains", [])
            node_count = result.get("node_count", 0)
            relationship_count = result.get("relationship_count", 0)
            
            message = "✅ 文档分析完成！\n\n"
            message += f"📊 统计信息:\n"
            message += f"• 节点数量: {node_count}\n"
            message += f"• 关系数量: {relationship_count}\n"
            message += f"• 事件链数量: {len(event_chains)}\n\n"
            
            if event_chains:
                message += "🔗 提取的事件链（前5条）:\n\n"
                for i, chain in enumerate(event_chains[:5], 1):
                    source = chain.get("source", "")
                    relation = chain.get("relation", "")
                    target = chain.get("target", "")
                    confidence = chain.get("confidence", 0)
                    
                    message += f"{i}. {source} → {relation} → {target}\n"
                    message += f"   置信度: {confidence:.2f}\n\n"
                
                if len(event_chains) > 5:
                    message += f"... 还有 {len(event_chains) - 5} 条事件链\n\n"
            
            message += "💡 提示: 使用 /火瞳查询 命令可以查询提取的信息"
            
            return message
            
        except Exception as e:
            logger.error(f"[UploadHandler] Format error: {e}")
            return f"✅ 分析完成，但结果格式化失败: {str(e)}"
    
    def _get_upload_instructions(self) -> str:
        """获取上传说明"""
        return """📤 火瞳文件上传

请发送文件以进行分析。

支持的文件格式:
• PDF (.pdf)
• 文本文件 (.txt)
• Word 文档 (.docx)

文件大小限制: 10MB

使用方法:
1. 直接发送文件（不需要命令）
2. 或者使用命令: /火瞳上传 然后发送文件

示例:
直接在聊天中发送火灾调查报告文件即可

⚠️ 注意:
• 文件分析需要30-60秒
• 系统会自动提取事件链并存入知识图谱
• 分析完成后可使用 /火瞳查询 命令查询"""
