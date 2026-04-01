"""
File Handler 单元测试
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.file_handler import FileHandler


class TestFileHandler:
    """文件处理器测试"""
    
    @pytest.fixture
    def handler(self):
        """创建文件处理器实例"""
        temp_dir = tempfile.mkdtemp()
        return FileHandler(temp_dir=temp_dir, max_file_size=10485760)
    
    def test_init(self, handler):
        """测试初始化"""
        assert handler.max_file_size == 10485760
        assert os.path.exists(handler.temp_dir)
    
    def test_validate_file_type_valid(self, handler):
        """测试验证有效文件类型"""
        assert handler.validate_file_type("document.pdf") is True
        assert handler.validate_file_type("report.docx") is True
        assert handler.validate_file_type("data.txt") is True
    
    def test_validate_file_type_invalid(self, handler):
        """测试验证无效文件类型"""
        assert handler.validate_file_type("image.jpg") is False
        assert handler.validate_file_type("script.py") is False
        assert handler.validate_file_type("archive.zip") is False
    
    def test_validate_file_size_valid(self, handler):
        """测试验证有效文件大小"""
        # 创建一个小文件
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = f.name
        
        try:
            assert handler.validate_file_size(temp_path) is True
        finally:
            os.unlink(temp_path)
    
    def test_validate_file_size_invalid(self, handler):
        """测试验证无效文件大小"""
        # 创建一个大文件（模拟）
        handler.max_file_size = 100  # 设置很小的限制
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"x" * 200)
            temp_path = f.name
        
        try:
            assert handler.validate_file_size(temp_path) is False
        finally:
            os.unlink(temp_path)
    
    def test_cleanup_temp_file(self, handler):
        """测试清理临时文件"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(dir=handler.temp_dir, delete=False) as f:
            temp_path = f.name
            f.write(b"test")
        
        assert os.path.exists(temp_path)
        
        # 清理文件
        handler.cleanup_temp_file(temp_path)
        
        assert not os.path.exists(temp_path)
    
    def test_cleanup_nonexistent_file(self, handler):
        """测试清理不存在的文件"""
        # 不应该抛出异常
        handler.cleanup_temp_file("/nonexistent/file.txt")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
