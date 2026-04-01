"""
Fire-Eye API 客户端
处理与 Fire-Eye 后端的所有 HTTP 通信
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional
from loguru import logger


class APIClient:
    """Fire-Eye API 客户端"""
    
    def __init__(
        self,
        api_url: str,
        api_key: str,
        timeout: int = 30,
        retries: int = 3
    ):
        """
        初始化 API 客户端
        
        Args:
            api_url: API 基础 URL
            api_key: API 密钥
            timeout: 请求超时时间（秒）
            retries: 失败重试次数
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.retries = retries
        self._session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"APIClient initialized: url={api_url}, timeout={timeout}s")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 aiohttp 会话"""
        if self._session is None or self._session.closed:
            timeout_config = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout_config,
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                }
            )
        return self._session
    
    async def close(self):
        """关闭客户端连接"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("APIClient session closed")
    
    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求（带重试逻辑）
        
        Args:
            method: HTTP 方法
            endpoint: API 端点
            **kwargs: 其他请求参数
            
        Returns:
            响应 JSON 数据
            
        Raises:
            Exception: 请求失败
        """
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        session = await self._get_session()
        
        last_error = None
        for attempt in range(self.retries):
            try:
                logger.debug(f"Request attempt {attempt + 1}/{self.retries}: {method} {url}")
                
                async with session.request(method, url, **kwargs) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    logger.debug(f"Request successful: {method} {url}")
                    return data
                    
            except aiohttp.ClientError as e:
                last_error = e
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.retries}): {e}")
                
                if attempt < self.retries - 1:
                    # 指数退避
                    wait_time = 2 ** attempt
                    logger.debug(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
            
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error: {e}")
                break
        
        # 所有重试都失败
        error_msg = f"Request failed after {self.retries} attempts: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    async def query(
        self,
        query: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询知识图谱
        
        Args:
            query: 查询文本
            session_id: 可选的会话 ID
            
        Returns:
            查询结果
        """
        payload = {"query": query}
        if session_id:
            payload["session_id"] = session_id
        
        logger.info(f"Querying: '{query}' (session: {session_id})")
        
        response = await self._request_with_retry(
            "POST",
            "/chat/query",
            json=payload
        )
        
        return response
    
    async def analyze(
        self,
        text: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析文本内容
        
        Args:
            text: 文本内容
            session_id: 可选的会话 ID
            
        Returns:
            任务信息（包含 task_id）
        """
        payload = {"text": text}
        if session_id:
            payload["session_id"] = session_id
        
        logger.info(f"Analyzing text: {len(text)} characters (session: {session_id})")
        
        response = await self._request_with_retry(
            "POST",
            "/chat/analyze",
            json=payload
        )
        
        return response
    
    async def upload(
        self,
        file_path: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        上传文件进行分析
        
        Args:
            file_path: 文件路径
            session_id: 可选的会话 ID
            
        Returns:
            任务信息（包含 task_id 和 document_id）
        """
        logger.info(f"Uploading file: {file_path} (session: {session_id})")
        
        # 准备 multipart/form-data
        data = aiohttp.FormData()
        data.add_field('file', open(file_path, 'rb'))
        if session_id:
            data.add_field('session_id', session_id)
        
        response = await self._request_with_retry(
            "POST",
            "/chat/upload",
            data=data
        )
        
        return response
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态
        
        Args:
            task_id: 任务 ID
            
        Returns:
            任务状态信息
        """
        logger.debug(f"Getting task status: {task_id}")
        
        response = await self._request_with_retry(
            "GET",
            f"/chat/status/{task_id}"
        )
        
        return response
    
    async def get_stats(
        self,
        stat_type: Optional[str] = None,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取统计信息
        
        Args:
            stat_type: 统计类型
            time_range: 时间范围
            
        Returns:
            统计信息
        """
        params = {}
        if stat_type:
            params['stat_type'] = stat_type
        if time_range:
            params['time_range'] = time_range
        
        logger.info(f"Getting stats: type={stat_type}, range={time_range}")
        
        response = await self._request_with_retry(
            "GET",
            "/chat/stats",
            params=params
        )
        
        return response
