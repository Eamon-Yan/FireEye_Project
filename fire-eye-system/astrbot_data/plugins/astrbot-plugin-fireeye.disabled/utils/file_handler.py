"""
文件处理工具
处理文件下载、验证和上传
"""

import os
import aiohttp
import mimetypes
from pathlib import Path
from typing import Optional, Tuple
from astrbot.core import logger


class FileHandler:
    """文件处理器"""
    
    # 支持的文件类型
    SUPPORTED_TYPES = {
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    def __init__(self, temp_dir: str = "/tmp/fire-eye", max_file_size: int = 10485760):
        """
        初始化文件处理器
        
        Args:
            temp_dir: 临时文件目录
            max_file_size: 最大文件大小（字节），默认 10MB
        """
        self.temp_dir = Path(temp_dir)
        self.max_file_size = max_file_size
        
        # 创建临时目录
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[FileHandler] Temp directory: {self.temp_dir}")
    
    def validate_file_type(self, filename: str) -> Tuple[bool, str]:
        """
        验证文件类型
        
        Args:
            filename: 文件名
            
        Returns:
            (是否有效, 错误消息)
        """
        ext = Path(filename).suffix.lower()
        
        if ext not in self.SUPPORTED_TYPES:
            supported = ', '.join(self.SUPPORTED_TYPES.keys())
            return False, f"不支持的文件类型 {ext}。支持的类型: {supported}"
        
        return True, ""
    
    def validate_file_size(self, file_size: int) -> Tuple[bool, str]:
        """
        验证文件大小
        
        Args:
            file_size: 文件大小（字节）
            
        Returns:
            (是否有效, 错误消息)
        """
        if file_size > self.max_file_size:
            max_mb = self.max_file_size / 1024 / 1024
            actual_mb = file_size / 1024 / 1024
            return False, f"文件过大 ({actual_mb:.1f}MB)。最大允许: {max_mb:.1f}MB"
        
        return True, ""
    
    async def download_from_url(self, url: str, filename: str) -> Tuple[bool, str, Optional[Path]]:
        """
        从 URL 下载文件到临时目录
        
        Args:
            url: 文件 URL
            filename: 保存的文件名
            
        Returns:
            (是否成功, 消息, 文件路径)
        """
        try:
            # 验证文件类型
            valid, msg = self.validate_file_type(filename)
            if not valid:
                return False, msg, None
            
            # 生成唯一文件名
            import uuid
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = self.temp_dir / unique_filename
            
            logger.info(f"[FileHandler] Downloading from {url}")
            
            # 下载文件
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return False, f"下载失败: HTTP {response.status}", None
                    
                    # 检查文件大小
                    content_length = response.headers.get('Content-Length')
                    if content_length:
                        valid, msg = self.validate_file_size(int(content_length))
                        if not valid:
                            return False, msg, None
                    
                    # 保存文件
                    with open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
            
            logger.info(f"[FileHandler] File downloaded: {file_path}")
            return True, "文件下载成功", file_path
            
        except Exception as e:
            logger.error(f"[FileHandler] Download error: {e}")
            return False, f"下载失败: {str(e)}", None
    
    async def upload_to_backend(
        self,
        file_path: Path,
        api_url: str,
        api_key: str,
        session_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[dict]]:
        """
        上传文件到 Fire-Eye 后端
        
        Args:
            file_path: 文件路径
            api_url: API 基础 URL
            api_key: API 密钥
            session_id: 会话 ID（可选）
            
        Returns:
            (是否成功, 消息, 响应数据)
        """
        try:
            if not file_path.exists():
                return False, "文件不存在", None
            
            logger.info(f"[FileHandler] Uploading {file_path.name} to backend")
            
            # 准备表单数据
            data = aiohttp.FormData()
            data.add_field('file',
                          open(file_path, 'rb'),
                          filename=file_path.name,
                          content_type=self._get_content_type(file_path.name))
            
            if session_id:
                data.add_field('session_id', session_id)
            
            # 上传文件
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{api_url}/api/v1/chat/upload",
                    data=data,
                    headers={"X-API-Key": api_key},
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return False, f"上传失败: HTTP {response.status}", None
                    
                    result = await response.json()
                    logger.info(f"[FileHandler] Upload successful: {result}")
                    return True, "文件上传成功", result
            
        except Exception as e:
            logger.error(f"[FileHandler] Upload error: {e}")
            return False, f"上传失败: {str(e)}", None
    
    def cleanup_file(self, file_path: Path) -> bool:
        """
        清理临时文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功
        """
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"[FileHandler] Cleaned up: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"[FileHandler] Cleanup error: {e}")
            return False
    
    def _get_content_type(self, filename: str) -> str:
        """获取文件的 Content-Type"""
        ext = Path(filename).suffix.lower()
        return self.SUPPORTED_TYPES.get(ext, 'application/octet-stream')
