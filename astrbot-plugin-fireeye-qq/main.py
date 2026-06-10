"""
Fire-Eye QQ Plugin - Main Entry Point
火瞳 QQ 插件 - 主入口
"""

import os
import yaml
import aiohttp
from pathlib import Path
from loguru import logger
from astrbot.api import star
from astrbot.api.event import AstrMessageEvent, filter, MessageEventResult


class Main(star.Star):
    """Fire-Eye QQ 插件主类"""
    
    def __init__(self, context: star.Context):
        """初始化插件"""
        self.context = context
        
        # 配置
        self.plugin_config = None
        self.api_url = None
        self.api_key = None
        self.session = None
        
        # 组件
        self.api_client = None
        self.session_manager = None
        self.request_queue = None
        self.formatter = None
        
        # 加载配置
        self._load_config()
        
        # 初始化组件
        self._initialize_components()
        
        logger.info("[Fire-Eye QQ] Plugin initialized")
        logger.info(f"[Fire-Eye QQ] API URL: {self.api_url}")
    
    def _load_config(self):
        """加载配置文件"""
        try:
            config_path = Path(__file__).parent / "config.yaml"
            
            if not config_path.exists():
                logger.error(f"[Fire-Eye QQ] Configuration file not found: {config_path}")
                # 从环境变量读取，无则报错
                self.api_url = os.environ.get('FIRE_EYE_API_URL', 'http://fire-eye-backend:8000/api/v1')
                self.api_key = os.environ.get('FIRE_EYE_API_KEY')
                if not self.api_key:
                    raise ValueError("FIRE_EYE_API_KEY 未设置：请在环境变量或 config.yaml 中配置 api_key")
                return
            
            with open(config_path, 'r', encoding='utf-8') as f:
                self.plugin_config = yaml.safe_load(f)
            
            # 提取配置
            fire_eye_config = self.plugin_config.get('fire_eye', {})
            self.api_url = fire_eye_config.get('api_url') or os.environ.get('FIRE_EYE_API_URL', 'http://fire-eye-backend:8000/api/v1')
            self.api_key = fire_eye_config.get('api_key') or os.environ.get('FIRE_EYE_API_KEY')
            if not self.api_key:
                raise ValueError("FIRE_EYE_API_KEY 未设置：请在 config.yaml 的 fire_eye.api_key 或环境变量中配置")
            
            logger.info("[Fire-Eye QQ] Configuration loaded successfully")
            
        except Exception as e:
            logger.error(f"[Fire-Eye QQ] Failed to load config: {e}")
            # 从环境变量读取
            self.api_url = os.environ.get('FIRE_EYE_API_URL', 'http://fire-eye-backend:8000/api/v1')
            self.api_key = os.environ.get('FIRE_EYE_API_KEY')
            if not self.api_key:
                raise ValueError(f"FIRE_EYE_API_KEY 未设置：配置加载失败且环境变量也未设置 ({e})")
    
    def _initialize_components(self):
        """初始化组件"""
        try:
            # 导入组件
            from .api.client import APIClient
            from .session.manager import SessionManager
            from .queue.request_queue import RequestQueue
            from .utils.formatter import MessageFormatter
            
            # 初始化 API 客户端
            self.api_client = APIClient(
                api_url=self.api_url,
                api_key=self.api_key,
                timeout=30
            )
            
            # 初始化会话管理器
            session_config = self.plugin_config.get('session', {}) if self.plugin_config else {}
            self.session_manager = SessionManager(
                session_ttl=session_config.get('ttl', 1800)
            )
            
            # 初始化请求队列
            queue_config = self.plugin_config.get('request_queue', {}) if self.plugin_config else {}
            self.request_queue = RequestQueue(
                max_concurrent=queue_config.get('max_concurrent', 5),
                max_queue_size=queue_config.get('max_queue_size', 20)
            )
            
            # 初始化消息格式化器
            qq_config = self.plugin_config.get('qq', {}) if self.plugin_config else {}
            self.formatter = MessageFormatter(
                max_message_length=qq_config.get('max_message_length', 4096),
                platform='qq'
            )
            
            logger.info("[Fire-Eye QQ] All components initialized")
            
        except Exception as e:
            logger.error(f"[Fire-Eye QQ] Component initialization error: {e}")
            raise
    
    async def _get_session(self):
        """获取或创建 aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"X-API-Key": self.api_key}
            )
        return self.session
    
    # ==================== 命令处理器 ====================
    
    @filter.command("火瞳帮助", alias={"ht帮助"})
    async def help_command(self, event: AstrMessageEvent, message: str = ""):
        """帮助命令"""
        try:
            logger.info("[Fire-Eye QQ] Help command triggered")
            
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
            
            event.set_result(MessageEventResult().message(help_text))
            
        except Exception as e:
            logger.error(f"[Fire-Eye QQ] Help command error: {e}")
            event.set_result(MessageEventResult().message(f"❌ 帮助命令执行失败: {str(e)}"))
    
    @filter.command("火瞳查询", alias={"ht查询"})
    async def query_command(self, event: AstrMessageEvent, message: str = ""):
        """查询命令"""
        try:
            # 获取查询文本
            query_text = message.strip() if message else event.message_str.strip()
            
            # 移除命令前缀
            for prefix in ["/火瞳查询", "/ht查询", "火瞳查询", "ht查询"]:
                if query_text.startswith(prefix):
                    query_text = query_text[len(prefix):].strip()
                    break
            
            if not query_text:
                event.set_result(MessageEventResult().message("❌ 请提供查询内容\n示例: /火瞳查询 火灾"))
                return
            
            logger.info(f"[Fire-Eye QQ] Query command: {query_text}")
            
            # 获取用户 ID - QQ 官方频道使用不同的属性
            try:
                if hasattr(event, 'user_id'):
                    user_id = str(event.user_id)
                elif hasattr(event, 'sender') and hasattr(event.sender, 'user_id'):
                    user_id = str(event.sender.user_id)
                elif hasattr(event, 'author'):
                    user_id = str(event.author.get('id', 'unknown'))
                else:
                    user_id = "unknown"
            except Exception as e:
                logger.warning(f"[Fire-Eye QQ] Failed to get user_id: {e}")
                user_id = "unknown"
            
            # 获取或创建会话
            session_id = self.session_manager.get_session(user_id)
            if not session_id:
                session_id = self.session_manager.create_session(user_id, "qq")
            
            # 发送"处理中"提示
            event.set_result(MessageEventResult().message("🔍 正在查询，请稍候..."))
            
            # 调用后端 API
            try:
                result = await self.api_client.query(
                    query=query_text,
                    session_id=session_id
                )
                
                if not result:
                    event.set_result(MessageEventResult().message("❌ 查询失败，请稍后重试"))
                    return
                
                # 解析结果
                if result.get("status") == "success":
                    data = result.get("data", {})
                    results = data.get("results", [])
                    
                    if not results:
                        response = f"🔍 查询: {query_text}\n\n未找到相关信息"
                    else:
                        response = f"🔍 查询: {query_text}\n\n找到 {len(results)} 条结果:\n\n"
                        
                        for i, item in enumerate(results[:5], 1):  # 只显示前5条
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
                    
                    # 更新会话活动时间
                    self.session_manager.update_activity(user_id)
                    
                    event.set_result(MessageEventResult().message(response))
                else:
                    error_msg = result.get("detail", "未知错误")
                    event.set_result(MessageEventResult().message(f"❌ 查询失败: {error_msg}"))
                    
            except Exception as e:
                logger.error(f"[Fire-Eye QQ] API call error: {e}")
                event.set_result(MessageEventResult().message(f"❌ 查询失败: {str(e)}"))
                
        except Exception as e:
            logger.error(f"[Fire-Eye QQ] Query command error: {e}")
            event.set_result(MessageEventResult().message(f"❌ 查询命令执行失败: {str(e)}"))
    
    @filter.command("火瞳统计", alias={"ht统计"})
    async def stats_command(self, event: AstrMessageEvent, message: str = ""):
        """统计命令"""
        try:
            logger.info("[Fire-Eye QQ] Stats command triggered")
            
            # 发送"处理中"提示
            event.set_result(MessageEventResult().message("📊 正在获取统计信息，请稍候..."))
            
            # 调用后端 API
            try:
                result = await self.api_client.get_stats()
                
                if not result:
                    event.set_result(MessageEventResult().message("❌ 获取统计信息失败，请稍后重试"))
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
                    
                    # 节点类型统计
                    node_types = data.get('node_types', {})
                    if node_types:
                        response += "📋 节点类型分布:\n"
                        for node_type, count in node_types.items():
                            response += f"• {node_type}: {count}\n"
                        response += "\n"
                    
                    # 关系类型统计
                    rel_types = data.get('relationship_types', {})
                    if rel_types:
                        response += "🔗 关系类型分布:\n"
                        for rel_type, count in rel_types.items():
                            response += f"• {rel_type}: {count}\n"
                    
                    event.set_result(MessageEventResult().message(response))
                else:
                    error_msg = result.get("detail", "未知错误")
                    event.set_result(MessageEventResult().message(f"❌ 获取统计信息失败: {error_msg}"))
                    
            except Exception as e:
                logger.error(f"[Fire-Eye QQ] API call error: {e}")
                event.set_result(MessageEventResult().message(f"❌ 获取统计信息失败: {str(e)}"))
                
        except Exception as e:
            logger.error(f"[Fire-Eye QQ] Stats command error: {e}")
            event.set_result(MessageEventResult().message(f"❌ 统计命令执行失败: {str(e)}"))
    
    async def __del__(self):
        """清理资源"""
        if self.session and not self.session.closed:
            await self.session.close()
        if self.api_client:
            await self.api_client.close()
