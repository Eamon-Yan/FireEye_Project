"""
Fire-Eye AstrBot Plugin - Full Implementation
火瞳系统 AstrBot 插件 - 完整实现
"""

import os
import yaml
import aiohttp
from pathlib import Path
from loguru import logger
from astrbot.api import star
from astrbot.api.event import AstrMessageEvent, filter, MessageEventResult
from astrbot.core import logger as astrbot_logger


class Main(star.Star):
    """Fire-Eye 插件主类"""
    
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
        self.file_handler = None
        self.session_manager = None
        self.task_poller = None
        
        # 加载配置
        self._load_config()
        
        # 初始化组件
        self._initialize_components()
        
        logger.info("[Fire-Eye] Plugin initialized")
        logger.info(f"[Fire-Eye] API URL: {self.api_url}")
    
    def _load_config(self):
        """加载配置文件"""
        try:
            config_path = Path(__file__).parent / "config.yaml"
            
            if not config_path.exists():
                logger.error(f"[Fire-Eye] Configuration file not found: {config_path}")
                # 从环境变量读取
                self.api_url = os.environ.get('FIRE_EYE_API_URL', 'http://fire-eye-backend:8000/api/v1')
                self.api_key = os.environ.get('FIRE_EYE_API_KEY')
                if not self.api_key:
                    raise ValueError("FIRE_EYE_API_KEY 未设置：请设置环境变量 FIRE_EYE_API_KEY")
                return
            
            with open(config_path, 'r', encoding='utf-8') as f:
                self.plugin_config = yaml.safe_load(f)
            
            # 提取配置
            fire_eye_config = self.plugin_config.get('fire_eye', {})
            self.api_url = fire_eye_config.get('api_url') or os.environ.get('FIRE_EYE_API_URL', 'http://fire-eye-backend:8000/api/v1')
            self.api_key = fire_eye_config.get('api_key') or os.environ.get('FIRE_EYE_API_KEY')
            if not self.api_key:
                raise ValueError("FIRE_EYE_API_KEY 未设置：请在 config.yaml 或环境变量中配置")
            
            logger.info("[Fire-Eye] Configuration loaded successfully")
            
        except Exception as e:
            logger.error(f"[Fire-Eye] Failed to load config: {e}")
            # 从环境变量读取
            self.api_url = os.environ.get('FIRE_EYE_API_URL', 'http://fire-eye-backend:8000/api/v1')
            self.api_key = os.environ.get('FIRE_EYE_API_KEY')
            if not self.api_key:
                raise ValueError(f"FIRE_EYE_API_KEY 未设置：配置加载失败且环境变量也未设置 ({e})")
    
    def _initialize_components(self):
        """初始化组件"""
        try:
            # 导入组件
            from api.client import APIClient
            from api.polling import TaskPoller
            from utils.file_handler import FileHandler
            from session.manager import SessionManager
            
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
            
            logger.info("[Fire-Eye] All components initialized")
            
        except Exception as e:
            logger.error(f"[Fire-Eye] Component initialization error: {e}")
            # 组件初始化失败不影响基本命令功能
            self.api_client = None
            self.file_handler = None
            self.session_manager = None
            self.task_poller = None
    
    async def _get_session(self):
        """获取或创建 aiohttp session"""
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
            
            logger.info(f"[Fire-Eye] Calling API: {method} {url}")
            
            if method == "GET":
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        error_text = await resp.text()
                        logger.error(f"[Fire-Eye] API error: {resp.status} - {error_text}")
                        return None
            elif method == "POST":
                async with session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        error_text = await resp.text()
                        logger.error(f"[Fire-Eye] API error: {resp.status} - {error_text}")
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
   /ht查询 <查询内容>
   示例: /火瞳查询 火灾

2️⃣ 上传命令
   /火瞳上传
   /ht上传
   上传文件进行分析（支持 PDF/TXT/DOCX）

3️⃣ 统计命令
   /火瞳统计
   /ht统计
   查看系统统计信息

4️⃣ 帮助命令
   /火瞳帮助
   /ht帮助
   显示此帮助信息

💡 提示:
- 使用 /ht 作为 /火瞳 的简写
- 查询支持关键词搜索
- 上传文件后会自动分析并提取事件链
- 系统会自动记录对话上下文

📞 需要帮助？请联系系统管理员"""
            
            event.set_result(MessageEventResult().message(help_text))
            
        except Exception as e:
            logger.error(f"[Fire-Eye] Help command error: {e}")
            event.set_result(MessageEventResult().message(f"❌ 帮助命令执行失败: {str(e)}"))
    
    @filter.command("火瞳查询", alias={"ht查询"})
    async def query_command(self, event: AstrMessageEvent):
        """查询命令"""
        try:
            # 获取查询文本
            query_text = event.message_str.strip()
            
            # 移除命令前缀
            for prefix in ["/火瞳查询", "/ht查询", "火瞳查询", "ht查询"]:
                if query_text.startswith(prefix):
                    query_text = query_text[len(prefix):].strip()
                    break
            
            if not query_text:
                event.set_result(MessageEventResult().message("❌ 请提供查询内容\n示例: /火瞳查询 火灾"))
                return
            
            logger.info(f"[Fire-Eye] Query command: {query_text}")
            
            # 调用后端 API
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
                
                event.set_result(MessageEventResult().message(response))
            else:
                error_msg = result.get("detail", "未知错误")
                event.set_result(MessageEventResult().message(f"❌ 查询失败: {error_msg}"))
                
        except Exception as e:
            logger.error(f"[Fire-Eye] Query command error: {e}")
            event.set_result(MessageEventResult().message(f"❌ 查询命令执行失败: {str(e)}"))
    
    @filter.command("火瞳统计", alias={"ht统计"})
    async def stats_command(self, event: AstrMessageEvent):
        """统计命令"""
        try:
            logger.info("[Fire-Eye] Stats command triggered")
            
            # 调用后端 API
            result = await self._call_api("chat/stats", method="GET")
            
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
            logger.error(f"[Fire-Eye] Stats command error: {e}")
            event.set_result(MessageEventResult().message(f"❌ 统计命令执行失败: {str(e)}"))
    
    @filter.command("火瞳上传", alias={"ht上传"})
    async def upload_command(self, event: AstrMessageEvent):
        """上传命令"""
        try:
            logger.info("[Fire-Eye] Upload command triggered")
            
            # 显示上传说明
            upload_instructions = """📤 火瞳文件上传

请发送文件以进行分析。

支持的文件格式:
• PDF (.pdf)
• 文本文件 (.txt)
• Word 文档 (.docx)

文件大小限制: 10MB

使用方法:
1. 发送 /火瞳上传 命令查看此说明
2. 直接发送文件（不需要再次输入命令）

示例:
直接在聊天中发送火灾调查报告文件即可

⚠️ 注意:
• 文件分析需要30-60秒
• 系统会自动提取事件链并存入知识图谱
• 分析完成后可使用 /火瞳查询 命令查询

💡 提示:
由于 Telegram 的限制，目前文件上传功能正在优化中。
您也可以通过 Web 界面上传文件：
http://localhost:3000/upload"""
            
            event.set_result(MessageEventResult().message(upload_instructions))
            
        except Exception as e:
            logger.error(f"[Fire-Eye] Upload command error: {e}")
            event.set_result(MessageEventResult().message(f"❌ 上传命令执行失败: {str(e)}"))
    
    async def __del__(self):
        """清理资源"""
        if self.session and not self.session.closed:
            await self.session.close()
