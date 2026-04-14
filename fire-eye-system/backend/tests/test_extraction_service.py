"""
智能抽取服务测试
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException

from app.services.extraction_service import (
    DocumentParser,
    SectionExtractor,
    ExtractionService,
    extraction_service
)
from app.schemas.document import FileType
from app.schemas.extraction import SectionType


class TestDocumentParser:
    """文档解析器测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.parser = DocumentParser()
    
    def test_supported_extensions(self):
        """测试支持的文件扩展名"""
        expected_extensions = {'.pdf', '.docx', '.txt'}
        actual_extensions = set(self.parser.supported_extensions.keys())
        assert actual_extensions == expected_extensions
    
    def test_parse_txt_file(self):
        """测试解析TXT文件"""
        # 创建临时TXT文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            test_content = "这是一个测试文档\n包含多行内容\n用于测试文档解析功能"
            f.write(test_content)
            temp_path = f.name
        
        try:
            result = self.parser.parse_document(temp_path, FileType.TXT)
            assert result == test_content
        finally:
            os.unlink(temp_path)
    
    def test_parse_txt_file_gbk_encoding(self):
        """测试解析GBK编码的TXT文件"""
        # 创建GBK编码的临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='gbk') as f:
            test_content = "这是GBK编码的测试文档"
            f.write(test_content)
            temp_path = f.name
        
        try:
            result = self.parser.parse_document(temp_path, FileType.TXT)
            assert test_content in result
        finally:
            os.unlink(temp_path)
    
    @patch('app.services.extraction_service.PyPDF2.PdfReader')
    def test_parse_pdf_file(self, mock_pdf_reader):
        """测试解析PDF文件"""
        # 模拟PDF页面
        mock_page = Mock()
        mock_page.extract_text.return_value = "PDF页面内容"
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader
        
        # 创建临时PDF文件
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            result = self.parser.parse_document(temp_path, FileType.PDF)
            assert "PDF页面内容" in result
        finally:
            os.unlink(temp_path)
    
    @patch('app.services.extraction_service.Document')
    def test_parse_docx_file(self, mock_document):
        """测试解析DOCX文件"""
        # 模拟DOCX段落
        mock_paragraph = Mock()
        mock_paragraph.text = "DOCX段落内容"
        
        mock_doc = Mock()
        mock_doc.paragraphs = [mock_paragraph]
        mock_document.return_value = mock_doc
        
        # 创建临时DOCX文件
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_path = f.name
        
        try:
            result = self.parser.parse_document(temp_path, FileType.DOCX)
            assert "DOCX段落内容" in result
        finally:
            os.unlink(temp_path)
    
    def test_parse_unsupported_file_type(self):
        """测试解析不支持的文件类型"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            temp_path = f.name
        
        try:
            with pytest.raises(HTTPException):
                self.parser.parse_document(temp_path, "unsupported")
        finally:
            os.unlink(temp_path)


class TestSectionExtractor:
    """章节提取器测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.extractor = SectionExtractor()
    
    def test_extract_sections_with_standard_headers(self):
        """测试提取标准章节标题的内容"""
        text = """
        火灾调查报告
        
        事故经过
        2023年3月15日上午10点，某工厂发生火灾。火势从车间开始蔓延，
        消防队及时赶到现场进行扑救。经过2小时的努力，火势得到控制。
        
        原因分析
        经过现场勘查和技术分析，确定火灾原因为电气线路老化导致短路起火。
        具体表现为配电箱内电线绝缘层破损，在负荷较大时产生电弧引燃周围可燃物。
        
        调查结果
        本次火灾属于电气火灾，责任在于企业安全管理不到位。
        """
        
        sections = self.extractor.extract_sections(text)
        
        assert SectionType.ACCIDENT_PROCESS.value in sections
        assert SectionType.CAUSE_ANALYSIS.value in sections
        assert SectionType.INVESTIGATION_RESULT.value in sections
        
        assert "2023年3月15日" in sections[SectionType.ACCIDENT_PROCESS.value]
        assert "电气线路老化" in sections[SectionType.CAUSE_ANALYSIS.value]
        assert "电气火灾" in sections[SectionType.INVESTIGATION_RESULT.value]
    
    def test_extract_sections_with_alternative_headers(self):
        """测试提取替代章节标题的内容"""
        text = """
        火灾情况
        工厂车间发生火灾，造成设备损坏。
        
        火灾原因
        电线老化导致短路起火。
        """
        
        sections = self.extractor.extract_sections(text)
        
        assert SectionType.ACCIDENT_PROCESS.value in sections
        assert SectionType.CAUSE_ANALYSIS.value in sections
        
        assert "工厂车间" in sections[SectionType.ACCIDENT_PROCESS.value]
        assert "电线老化" in sections[SectionType.CAUSE_ANALYSIS.value]
    
    def test_intelligent_section_split(self):
        """测试智能章节分割"""
        text = """
        这是第一段内容，描述了事故的基本情况。
        包含了时间、地点、人员等基本信息。
        
        这是第二段内容，分析了事故发生的原因。
        从技术角度进行了详细的分析和说明。
        
        这是第三段内容，提出了预防措施。
        包括技术改进和管理加强等方面。
        
        这是第四段内容，总结了调查结果。
        明确了责任归属和处理意见。
        """
        
        sections = self.extractor.extract_sections(text)
        
        # 应该至少有事故经过章节
        assert len(sections) > 0
        assert SectionType.ACCIDENT_PROCESS.value in sections
    
    def test_preprocess_text(self):
        """测试文本预处理"""
        text = "第一行\r\n\r\n第二行\r第三行\n\n\n第四行"
        processed = self.extractor._preprocess_text(text)
        
        # 应该统一换行符并去除多余空白
        assert "\r" not in processed
        assert "\n\n\n" not in processed
    
    def test_clean_section_content(self):
        """测试章节内容清理"""
        content = """
        事故经过
        
        第 1 页
        
        实际内容开始
        这是有用的内容
        
        - 2 -
        
        更多有用内容
        """
        
        cleaned = self.extractor._clean_section_content(content)
        
        # 应该去除页码等无关内容
        assert "第 1 页" not in cleaned
        assert "- 2 -" not in cleaned
        assert "实际内容开始" in cleaned
        assert "有用的内容" in cleaned
    
    def test_is_header_footer(self):
        """测试页眉页脚识别"""
        assert self.extractor._is_header_footer("1")
        assert self.extractor._is_header_footer("第 5 页")
        assert self.extractor._is_header_footer("3/10")
        assert self.extractor._is_header_footer("- 7 -")
        
        assert not self.extractor._is_header_footer("这是正常的内容")
        assert not self.extractor._is_header_footer("事故经过详细描述")


class TestExtractionService:
    """智能抽取服务测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.service = ExtractionService()
    
    @pytest.mark.asyncio
    async def test_process_document_txt(self):
        """测试处理TXT文档"""
        # 创建模拟的上传文件
        mock_file = Mock()
        mock_file.filename = "test.txt"
        test_content = """
事故经过
2023年3月15日发生火灾事故，造成设备损坏。

原因分析
经过调查，确定是电气线路老化导致的火灾。
"""
        mock_file.read = AsyncMock(return_value=test_content.encode('utf-8'))
        
        with patch.object(self.service.parser, 'parse_document') as mock_parse:
            mock_parse.return_value = test_content
            
            document_id, sections = await self.service.process_document(mock_file)
            
            assert document_id is not None
            assert isinstance(sections.sections, dict)
            assert len(sections.sections) >= 2  # 应该至少有事故经过和原因分析
    
    @pytest.mark.asyncio
    async def test_process_document_unsupported_type(self):
        """测试处理不支持的文档类型"""
        mock_file = Mock()
        mock_file.filename = "test.xyz"
        
        with pytest.raises(Exception):
            await self.service.process_document(mock_file)
    
    def test_validate_sections_valid(self):
        """测试验证有效的章节内容"""
        sections = {
            SectionType.ACCIDENT_PROCESS.value: "这是一个足够长的事故经过描述，包含了详细的时间、地点、人员等信息。",
            SectionType.CAUSE_ANALYSIS.value: "这是一个足够长的原因分析内容，从技术角度分析了事故发生的根本原因。"
        }
        
        errors = self.service.validate_sections(sections)
        assert len(errors) == 0
    
    def test_validate_sections_missing_required(self):
        """测试验证缺少必需章节的情况"""
        sections = {
            SectionType.INVESTIGATION_RESULT.value: "只有调查结果，缺少必需章节"
        }
        
        errors = self.service.validate_sections(sections)
        assert len(errors) > 0
        assert any("缺少必需章节" in error for error in errors)
    
    def test_validate_sections_content_too_short(self):
        """测试验证章节内容过短的情况"""
        sections = {
            SectionType.ACCIDENT_PROCESS.value: "太短",
            SectionType.CAUSE_ANALYSIS.value: "也太短"
        }
        
        errors = self.service.validate_sections(sections)
        assert len(errors) > 0
        assert any("章节内容过短" in error for error in errors)
    
    def test_get_document_path(self):
        """测试获取文档路径"""
        document_id = "test-doc-123"
        file_extension = ".pdf"
        
        path = self.service.get_document_path(document_id, file_extension)
        
        assert str(path).endswith(f"{document_id}{file_extension}")
        assert path.parent == self.service.upload_dir


class TestGlobalService:
    """全局服务实例测试"""
    
    def test_extraction_service_instance(self):
        """测试全局抽取服务实例"""
        assert extraction_service is not None
        assert isinstance(extraction_service, ExtractionService)
        assert hasattr(extraction_service, 'parser')
        assert hasattr(extraction_service, 'extractor')
