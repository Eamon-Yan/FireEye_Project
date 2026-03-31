"""
Fire-Eye QQ Plugin - Debug Version
用于诊断命令处理问题
"""

import yaml
import aiohttp
from pathlib import Path
from loguru import logger
from astrbot.api import star
from astrbot.api.event import AstrMessageEvent, filter, MessageEventResult


class Main(star.Star):
    """Fire-Eye QQ 插件主类 - 调试版本"""
    
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
        
        logger.info("[Fire-Eye QQ DEBUG] Plugin initialized")
        logger.info(f"[Fire-Eye QQ DEBUG] API URL: {self.api_url}")
        logger.info(f"[Fire-Eye QQ DEBUG] API Key: {self.api_key[:20]}...")
    
    def _load_config(self):
        """加载配置文件"""
        try:
            config_path = Path(__file__).parent / "config.yaml"
            
            if not config_path.exists():
                logger.error(f"[Fire-Eye QQ DEBUG] Configuration file not found: {config_path}")
                self.api_url = "http://127.0.0.1:8000/api/v1"
                self.api_key = "smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA"
                return
            
            with open(config_path, 'r', encoding='utf-8') as f:
                self.plugin_config = yaml.safe_load(f)
            
            fire_eye_config = self.plugin_config.get('fire_eye', {})
            self.api_url = fire_eye_config.get('api_url', 'http://127.0.0.1:8000/api/v1')
            self.api_key = fire_eye_config.get('api_key', 'smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA')
            
            logger.info(f"[Fire-Eye QQ DEBUG] Config loaded from {config_path}")
            
        except Exception as e:
            logger.error(f"[Fire-Eye QQ DEBUG] Failed to load config: {e}")
            self.api_url = "http://127.0.0.1:8000/api/v1"
            self.api_key = "smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA"
    
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
                timeout=30,
                retries=3
            )
            
            # 初始化会话管理器
            self.session_manager = SessionManager()
            
            # 初始化请求队列
            self.request_queue = RequestQueue(max_concurrent=5, max_queue_size=20)
            
            # 初始化消息格式化器
            self.formatter = MessageFormatter()
            
            logger.info("[Fire-Eye QQ DEBUG] All components initialized successfully")
            
        except Exception as e:
            logger.error(f"[Fire-Eye QQ DEBUG] Failed to initialize components: {e}")
            raise
    
    async def _get_session(self):
        """获取或创建会话"""
        # 这是一个占位符方法
        return None
    
    # ==================== 消息事件处理 ====================
    
    @filter.message()
    async def on_message(self, event: AstrMessageEvent):
        """处理所有消息事件 - 用于调试"""
        try:
            message = event.message_str.strip()
            user_id = str(event.sender.user_id) if hasattr(event.sender, 'user_id') else "unknown"
            
            logger.info(f"[Fire-Eye QQ DEBUG] Message received from {user_id}: {message}")
            
            # 检查是否是火瞳命令
            if message.startswith(("/火瞳", "/ht", "火瞳", "ht")):
                logger.info(f"[Fire-Eye QQ DEBUG] Fire-Eye command detected: {message}")
            
        except Exception as e:
            logger.error(f"[Fire-Eye QQ DEBUG] Error in on_message: {e}")
    
    # ==================== 命令处理器 ====================
    
    @filter.command("火瞳帮助", alias={"ht帮助"})
    async def help_command(self, event: AstrMessageEvent):
        """帮助命令"""
        try:
            logger.info("[Fire-Eye QQ DEBUG] Help command triggered")
            
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
            logger.error(f"[Fire-Eye QQ DEBUG] Help command error: {e}")
            event.set_result(MessageEventResult().message(f"❌ 帮助命令执行失败: {str(e)}"))
    
    @filter.command("火瞳查询", alias={"ht查询"})
    async def query_command(self, event: AstrMessageEvent):
        """查询命令"""
        try:
            logger.info(f"[Fire-Eye QQ DEBUG] Query command triggered")
            logger.info(f"[Fire-Eye QQ DEBUG] Message: {event.message_str}")
            
            # 获取查询文本
            query_text = event.message_str.strip()
            
            # 移除命令前缀
            for prefix in ["/火瞳查询", "/ht查询", "火瞳查询", "ht查询"]:
                if query_text.startswith(prefix):
                    query_text = query_text[len(prefix):].strip()
                    break
            
            if not query_text:
                logger.warning("[Fire-Eye QQ DEBUG] No query text provided")
                event.set_result(MessageEventResult().message("❌ 请提供查询内容\n示例: /火瞳查询 火灾"))
                return
            
            logger.info(f"[Fire-Eye QQ DEBUG] Query text: {query_text}")
            
            # 获取用户 ID
            user_id = str(event.sender.user_id) if hasattr(event.sender, 'user_id') else "unknown"
            logger.info(f"[Fire-Eye QQ DEBUG] User ID: {user_id}")
            
            # 发送"处理中"提示
            event.set_result(MessageEventResult().message("🔍 正在查询，请稍候..."))
            
            # 调用后端 API
            try:
                logger.info(f"[Fire-Eye QQ DEBUG] Calling API: {self.api_url}/chat/query")
                
                result = await self.api_client.query(
                    query=query_text,
                    session_id=None
                )
                
                logger.info(f"[Fire-Eye QQ DEBUG] API response: {result}")
                
                if not result:
                    logger.error("[Fire-Eye QQ DEBUG] Empty API response")
                    event.set_result(MessageEventResult().message("❌ 查询失败，请稍后重试"))
                    return
                
                # 解析结果
                if result.get("status") == "success":
                    data = result.get("data", {})
                    results = data.get("results", [])
                    
                    logger.info(f"[Fire-Eye QQ DEBUG] Found {len(results)} results")
                    
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
                    
                    logger.info(f"[Fire-Eye QQ DEBUG] Sending response: {response[:100]}...")
                    event.set_result(MessageEventResult().message(response))
                else:
                    error_msg = result.get("detail", "未知错误")
                    logger.error(f"[Fire-Eye QQ DEBUG] API error: {error_msg}")
                    event.set_result(MessageEventResult().message(f"❌ 查询失败: {error_msg}"))
                    
            except Exception as e:
                logger.error(f"[Fire-Eye QQ DEBUG] API call error: {e}", exc_info=True)
                event.set_result(MessageEventResult().message(f"❌ 查询失败: {str(e)}"))
                
        except Exception as e:
            logger.error(f"[Fire-Eye QQ DEBUG] Query command error: {e}", exc_info=True)
            event.set_result(MessageEventResult().message(f"❌ 查询命令执行失败: {str(e)}"))
    
    @filter.command("火瞳统计", alias={"ht统计"})
    async def stats_command(self, event: AstrMessageEvent):
        """统计命令"""
        try:
            logger.info("[Fire-Eye QQ DEBUG] Stats command triggered")
            
            # 发送"处理中"提示
            event.set_result(MessageEventResult().message("📊 正在获取统计信息，请稍候..."))
            
            # 调用后端 API
            try:
                logger.info(f"[Fire-Eye QQ DEBUG] Calling API: {self.api_url}/chat/stats")
                
                result = await self.api_client.get_stats()
                
                logger.info(f"[Fire-Eye QQ DEBUG] API response: {result}")
                
                if not result:
                    logger.error("[Fire-Eye QQ DEBUG] Empty API response")
                    event.set_result(MessageEventResult().message("❌ 获取统计失败，请稍后重试"))
                    return
                
                # 解析结果
                if result.get("status") == "success":
                    data = result.get("data", {})
                    
                    response = "📊 火瞳系统统计信息\n\n"
                    response += "📈 数据概览:\n"
                    response += f"• 事件总数: {data.get('total_events', 0)}\n"
                    response += f"• 实体总数: {data.get('total_entities', 0)}\n"
                    response += f"• 关系总数: {data.get('total_relationships', 0)}\n"
                    
                    node_types = data.get('node_types', {})
                    if node_types:
                        response += "\n📊 节点类型:\n"
                        for node_type, count in node_types.items():
                            response += f"• {node_type}: {count}\n"
                    
                    logger.info(f"[Fire-Eye QQ DEBUG] Sending response: {response[:100]}...")
                    event.set_result(MessageEventResult().message(response))
                else:
                    error_msg = result.get("detail", "未知错误")
                    logger.error(f"[Fire-Eye QQ DEBUG] API error: {error_msg}")
                    event.set_result(MessageEventResult().message(f"❌ 获取统计失败: {error_msg}"))
                    
            except Exception as e:
                logger.error(f"[Fire-Eye QQ DEBUG] API call error: {e}", exc_info=True)
                event.set_result(MessageEventResult().message(f"❌ 获取统计失败: {str(e)}"))
                
        except Exception as e:
            logger.error(f"[Fire-Eye QQ DEBUG] Stats command error: {e}", exc_info=True)
            event.set_result(MessageEventResult().message(f"❌ 统计命令执行失败: {str(e)}"))
    
    async def __del__(self):
        """清理资源"""
        try:
            if self.api_client:
                await self.api_client.close()
            logger.info("[Fire-Eye QQ DEBUG] Plugin cleaned up")
        except Exception as e:
            logger.error(f"[Fire-Eye QQ DEBUG] Error during cleanup: {e}")
