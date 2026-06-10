"""
Fire-Eye AstrBot Plugin - Correct Implementation
火瞳系统 AstrBot 插件 - 正确实现
"""

import os
import yaml
import aiohttp
from pathlib import Path
from astrbot.api import star
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.core import logger

# 导入新模块（使用相对导入）
from .api.client import APIClient
from .api.polling import TaskPoller
from .utils.file_handler import FileHandler
from .session.manager import SessionManager
from .commands.upload_handler import UploadHandler


class Main(star.Star):
    """Fire-Eye 插件主类"""
    
    def __init__(self, context: star.Context):
        """初始化插件"""
        self.context = context
        
        self.plugin_config = None
        self.api_url = None
        self.api_key = None
        self.session = None
        
        # 新组件
        self.api_client = None
        self.task_poller = None
        self.file_handler = None
        self.session_manager = None
        self.upload_handler = None
        
        self._load_config()
        self._initialize_components()
        
        logger.info("[Fire-Eye] Plugin initialized")
        logger.info(f"[Fire-Eye] API URL: {self.api_url}")
    
    def _load_config(self):
        """加载配置文件"""
        try:
            config_path = Path(__file__).parent / "config.yaml"
            
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.plugin_config = yaml.safe_load(f)
                
                fire_eye_config = self.plugin_config.get('fire_eye', {})
                self.api_url = fire_eye_config.get('api_url') or os.environ.get('FIRE_EYE_API_URL', 'http://fire-eye-backend:8000/api/v1')
                self.api_key = fire_eye_config.get('api_key') or os.environ.get('FIRE_EYE_API_KEY')
                if not self.api_key:
                    raise ValueError("FIRE_EYE_API_KEY 未设置")
                logger.info("[Fire-Eye] Configuration loaded")
            else:
                # 从环境变量读取
                self.api_url = os.environ.get('FIRE_EYE_API_URL', 'http://fire-eye-backend:8000/api/v1')
                self.api_key = os.environ.get('FIRE_EYE_API_KEY')
                if not self.api_key:
                    raise ValueError("FIRE_EYE_API_KEY 未设置：请设置环境变量")
                logger.warning("[Fire-Eye] Using environment configuration")
                
        except Exception as e:
            logger.error(f"[Fire-Eye] Config load error: {e}")
            self.api_url = os.environ.get('FIRE_EYE_API_URL', 'http://fire-eye-backend:8000/api/v1')
            self.api_key = os.environ.get('FIRE_EYE_API_KEY')
            if not self.api_key:
                raise ValueError(f"FIRE_EYE_API_KEY 未设置：配置加载失败 ({e})")
    
    def _initialize_components(self):
        """初始化组件"""
        try:
            # 初始化 API 客户端
            self.api_client = APIClient(
                api_url=self.api_url,
                api_key=self.api_key,
                timeout=30
            )
            
            # 初始化任务轮询器
            self.task_poller = TaskPoller(self.api_client)
            
            # 初始化文件处理器
            file_config = self.plugin_config.get('file_upload', {}) if self.plugin_config else {}
            self.file_handler = FileHandler(
                temp_dir=file_config.get('temp_dir', '/tmp/fire-eye'),
                max_file_size=file_config.get('max_file_size', 10485760)
            )
            
            # 初始化会话管理器
            session_config = self.plugin_config.get('session', {}) if self.plugin_config else {}
            self.session_manager = SessionManager(
                session_ttl=session_config.get('ttl', 1800)
            )
            
            # 初始化上传处理器
            self.upload_handler = UploadHandler(
                api_client=self.api_client,
                file_handler=self.file_handler,
                task_poller=self.task_poller,
                session_manager=self.session_manager
            )
            
            logger.info("[Fire-Eye] All components initialized")
            
        except Exception as e:
            logger.error(f"[Fire-Eye] Component initialization error: {e}")
            raise
    
    async def _get_session(self):
        """获取 HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"X-API-Key": self.api_key}
            )
        return self.session
    
    async def _call_api(self, endpoint: str, method: str = "GET", data: dict = None):
        """调用后端 API"""
        try:
            session = await self._get_session()
            url = f"{self.api_url}/{endpoint}"
            
            logger.info(f"[Fire-Eye] API call: {method} {url}")
            
            if method == "GET":
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    logger.error(f"[Fire-Eye] API error: {resp.status}")
                    return None
            elif method == "POST":
                async with session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    logger.error(f"[Fire-Eye] API error: {resp.status}")
                    return None
                        
        except Exception as e:
            logger.error(f"[Fire-Eye] API call failed: {e}")
            return None
    
    # ==================== 命令处理器 ====================
    
    @filter.command("火瞳帮助", alias={"ht帮助"})
    async def help_command(self, event: AstrMessageEvent):
        """帮助命令"""
        try:
            logger.info("[Fire-Eye] Help command triggered")
            
            help_text = """🔥 火瞳系统 - 帮助信息

📖 可用命令:

1️⃣ 查询命令
   /火瞳查询 <查询内容>
   示例: /火瞳查询 火灾

2️⃣ 上传命令
   /火瞳上传
   上传文件进行分析（支持 PDF/TXT/DOCX）

3️⃣ 统计命令
   /火瞳统计
   查看系统统计信息

4️⃣ 帮助命令
   /火瞳帮助
   显示此帮助信息

💡 提示:
- 查询支持关键词搜索
- 上传文件后会自动分析并提取事件链
- 系统会自动记录对话上下文

📞 需要帮助？请联系系统管理员"""
            
            from astrbot.api.event import MessageEventResult
            event.set_result(MessageEventResult().message(help_text))
            
        except Exception as e:
            logger.error(f"[Fire-Eye] Help error: {e}")
            from astrbot.api.event import MessageEventResult
            event.set_result(MessageEventResult().message(f"❌ 帮助命令失败: {str(e)}"))
    
    @filter.command("火瞳查询", alias={"ht查询"})
    async def query_command(self, event: AstrMessageEvent):
        """查询命令"""
        try:
            # 获取查询文本（去除命令部分）
            query_text = event.message_str.strip()
            
            # 移除命令前缀
            for prefix in ["/火瞳查询", "火瞳查询", "/ht查询", "ht查询"]:
                if query_text.startswith(prefix):
                    query_text = query_text[len(prefix):].strip()
                    break
            
            from astrbot.api.event import MessageEventResult
            
            if not query_text:
                event.set_result(MessageEventResult().message("❌ 请提供查询内容\n示例: /火瞳查询 火灾"))
                return
            
            logger.info(f"[Fire-Eye] Query: {query_text}")
            
            # 调用 API
            result = await self._call_api("chat/query", method="POST", data={"query": query_text})
            
            if not result:
                event.set_result(MessageEventResult().message("❌ 查询失败，请稍后重试"))
                return
            
            # 解析结果
            if result.get("status") == "success":
                data = result.get("data", {})
                results = data.get("results", [])
                session_id = data.get("session_id", "")
                
                if not results:
                    response = f"🔍 查询: {query_text}\n\n未找到相关信息"
                else:
                    response = f"🔍 查询: {query_text}\n\n找到 {len(results)} 条结果:\n\n"
                    
                    for i, item in enumerate(results[:5], 1):
                        node_type = item.get("type", "Unknown")
                        name = item.get("name", item.get("id", ""))
                        desc = item.get("description", "")
                        
                        response += f"{i}. [{node_type}] {name}\n"
                        if desc:
                            response += f"   {desc[:100]}...\n" if len(desc) > 100 else f"   {desc}\n"
                        response += "\n"
                    
                    if len(results) > 5:
                        response += f"... 还有 {len(results) - 5} 条结果\n"
                    
                    response += f"\n💬 会话ID: {session_id[:12]}..."
                
                event.set_result(MessageEventResult().message(response))
            else:
                error_msg = result.get("detail", "未知错误")
                event.set_result(MessageEventResult().message(f"❌ 查询失败: {error_msg}"))
                
        except Exception as e:
            logger.error(f"[Fire-Eye] Query error: {e}")
            from astrbot.api.event import MessageEventResult
            event.set_result(MessageEventResult().message(f"❌ 查询失败: {str(e)}"))
    
    @filter.command("火瞳统计", alias={"ht统计"})
    async def stats_command(self, event: AstrMessageEvent):
        """统计命令"""
        try:
            logger.info("[Fire-Eye] Stats command triggered")
            
            # 调用 API
            result = await self._call_api("chat/stats", method="GET")
            
            from astrbot.api.event import MessageEventResult
            
            if not result:
                event.set_result(MessageEventResult().message("❌ 获取统计信息失败"))
                return
            
            # 解析结果
            if result.get("status") == "success":
                data = result.get("data", {})
                
                response = """📊 火瞳系统统计信息

📈 数据概览:
"""
                response += f"• 事件总数: {data.get('total_events', 0)}\n"
                response += f"• 实体总数: {data.get('total_entities', 0)}\n"
                response += f"• 关系总数: {data.get('total_relationships', 0)}\n"
                response += f"• 文档总数: {data.get('total_documents', 0)}\n\n"
                
                # 节点类型
                node_types = data.get('node_types', {})
                if node_types:
                    response += "📋 节点类型:\n"
                    for node_type, count in node_types.items():
                        response += f"• {node_type}: {count}\n"
                    response += "\n"
                
                # 关系类型
                rel_types = data.get('relationship_types', {})
                if rel_types:
                    response += "🔗 关系类型:\n"
                    for rel_type, count in rel_types.items():
                        response += f"• {rel_type}: {count}\n"
                
                event.set_result(MessageEventResult().message(response))
            else:
                error_msg = result.get("detail", "未知错误")
                event.set_result(MessageEventResult().message(f"❌ 获取统计失败: {error_msg}"))
                
        except Exception as e:
            logger.error(f"[Fire-Eye] Stats error: {e}")
            from astrbot.api.event import MessageEventResult
            event.set_result(MessageEventResult().message(f"❌ 统计失败: {str(e)}"))
    
    @filter.command("火瞳上传", alias={"ht上传"})
    async def upload_command(self, event: AstrMessageEvent):
        """上传命令"""
        try:
            logger.info("[Fire-Eye] Upload command triggered")
            
            # 获取用户 ID - 使用更安全的方式
            try:
                if hasattr(event, 'message') and hasattr(event.message, 'sender'):
                    user_id = str(event.message.sender.id)
                elif hasattr(event, 'unified_msg_origin'):
                    user_id = str(event.unified_msg_origin)
                else:
                    user_id = "unknown"
            except Exception as e:
                logger.warning(f"[Fire-Eye] Could not get user_id: {e}")
                user_id = "unknown"
            
            # 调用上传处理器
            result = await self.upload_handler.handle(event, user_id)
            
            if result:
                from astrbot.api.event import MessageEventResult
                event.set_result(MessageEventResult().message(result))
                
        except Exception as e:
            logger.error(f"[Fire-Eye] Upload error: {e}", exc_info=True)
            from astrbot.api.event import MessageEventResult
            event.set_result(MessageEventResult().message(f"❌ 上传失败: {str(e)}"))
    
    @filter.message()
    async def handle_all_messages(self, event: AstrMessageEvent):
        """处理所有消息，检查文件上传"""
        try:
            # 检查是否有文件
            has_file = False
            
            if hasattr(event, 'message_obj') and hasattr(event.message_obj, 'chain'):
                for component in event.message_obj.chain:
                    component_type = type(component).__name__
                    if 'File' in component_type or 'Document' in component_type:
                        has_file = True
                        logger.info(f"[Fire-Eye] File detected in message: {component_type}")
                        break
            
            if not has_file:
                return  # 不是文件消息，跳过
            
            # 检查是否包含上传关键词
            message_text = event.message_str.lower() if event.message_str else ""
            if '火瞳上传' in message_text or 'ht上传' in message_text or '上传' in message_text:
                logger.info("[Fire-Eye] File upload detected via message handler")
                
                user_id = str(event.get_sender_id())
                result = await self.upload_handler.handle(event, user_id)
                
                if result:
                    from astrbot.api.event import MessageEventResult
                    event.set_result(MessageEventResult().message(result))
                    
        except Exception as e:
            logger.error(f"[Fire-Eye] Message handler error: {e}", exc_info=True)
    
    async def __del__(self):
        """清理资源"""
        if self.session and not self.session.closed:
            await self.session.close()
