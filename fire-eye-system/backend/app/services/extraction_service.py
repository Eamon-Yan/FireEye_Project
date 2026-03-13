"""
智能抽取服务
处理文档上传、解析和章节提取，集成校验对齐服务
"""

import os
import re
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import uuid
from datetime import datetime

import PyPDF2
from docx import Document
from fastapi import UploadFile, HTTPException

from app.core.config import settings
from app.schemas.extraction import (
    DocumentSections,
    ExtractionResult,
    ProcessingStatus,
    DocumentType,
    SectionType
)
from app.schemas.document import Document as DocumentModel, DocumentCreate, FileType
from app.schemas.event_chain import EventChainCreate
from app.services.llm_service import llm_service
from app.services.validation_service import validation_service

logger = logging.getLogger(__name__)


class DocumentParser:
    """文档解析器基类"""
    
    def __init__(self):
        self.supported_extensions = {
            '.pdf': FileType.PDF,
            '.docx': FileType.DOCX,
            '.doc': FileType.DOC,
            '.txt': FileType.TXT
        }
    
    def parse_document(self, file_path: str, file_type: FileType) -> str:
        """解析文档并提取文本内容"""
        try:
            if file_type == FileType.PDF:
                return self._parse_pdf(file_path)
            elif file_type == FileType.DOCX:
                return self._parse_docx(file_path)
            elif file_type == FileType.DOC:
                return self._parse_doc(file_path)
            elif file_type == FileType.TXT:
                return self._parse_txt(file_path)
            else:
                raise ValueError(f"不支持的文件类型: {file_type}")
        except Exception as e:
            logger.error(f"文档解析失败: {file_path}, 错误: {e}")
            raise HTTPException(status_code=400, detail=f"文档解析失败: {str(e)}")
    
    def _parse_pdf(self, file_path: str) -> str:
        """解析PDF文件"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"PDF解析失败: {file_path}, 错误: {e}")
            raise ValueError(f"PDF文件解析失败: {str(e)}")
        
        return text.strip()
    
    def _parse_docx(self, file_path: str) -> str:
        """解析DOCX文件"""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            logger.error(f"DOCX解析失败: {file_path}, 错误: {e}")
            raise ValueError(f"DOCX文件解析失败: {str(e)}")
        
        return text.strip()
    
    def _parse_doc(self, file_path: str) -> str:
        """解析DOC文件 (暂时不支持，建议转换为DOCX)"""
        raise ValueError("DOC格式暂不支持，请转换为DOCX格式")
    
    def _parse_txt(self, file_path: str) -> str:
        """解析TXT文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as file:
                    text = file.read()
            except Exception as e:
                logger.error(f"TXT解析失败: {file_path}, 错误: {e}")
                raise ValueError(f"TXT文件解析失败: {str(e)}")
        except Exception as e:
            logger.error(f"TXT解析失败: {file_path}, 错误: {e}")
            raise ValueError(f"TXT文件解析失败: {str(e)}")
        
        return text.strip()


class SectionExtractor:
    """章节提取器"""
    
    def __init__(self):
        # 定义章节识别的正则表达式模式
        self.section_patterns = {
            SectionType.ACCIDENT_PROCESS: [
                r'(?:^|\n)\s*(?:事故经过|事故过程|事故情况|事故描述|事故发生过程)\s*[：:]\s*',
                r'(?:^|\n)\s*(?:火灾经过|火灾过程|火灾情况|火灾发生过程)\s*[：:]\s*',
                r'(?:^|\n)\s*(?:起火经过|起火过程|起火情况)\s*[：:]\s*',
                r'(?:^|\n)\s*(?:燃烧过程|燃烧情况)\s*[：:]\s*',
                # 备用模式：不带冒号的标题
                r'(?:^|\n)\s*(?:事故经过|事故过程|事故情况|事故描述|事故发生过程)\s*(?:\n|$)',
                r'(?:^|\n)\s*(?:火灾经过|火灾过程|火灾情况|火灾发生过程)\s*(?:\n|$)',
            ],
            SectionType.CAUSE_ANALYSIS: [
                r'(?:^|\n)\s*(?:原因分析|事故原因|火灾原因|起火原因)\s*[：:]\s*',
                r'(?:^|\n)\s*(?:原因调查|原因查明|原因认定)\s*[：:]\s*',
                r'(?:^|\n)\s*(?:技术分析|专业分析)\s*[：:]\s*',
                # 备用模式：不带冒号的标题
                r'(?:^|\n)\s*(?:原因分析|事故原因|火灾原因|起火原因)\s*(?:\n|$)',
            ],
            SectionType.INVESTIGATION_RESULT: [
                r'(?:^|\n)\s*(?:调查结果|调查结论|调查认定)\s*[：:]\s*',
                r'(?:^|\n)\s*(?:事故认定|火灾认定)\s*[：:]\s*',
                r'(?:^|\n)\s*(?:调查情况)\s*[：:]\s*',
                # 备用模式：不带冒号的标题
                r'(?:^|\n)\s*(?:调查结果|调查结论|调查认定)\s*(?:\n|$)',
            ],
            SectionType.PREVENTION_MEASURES: [
                r'(?:^|\n)\s*(?:预防措施|防范措施|整改措施)\s*[：:]\s*',
                r'(?:^|\n)\s*(?:安全建议|安全措施|防火措施)\s*[：:]\s*',
                r'(?:^|\n)\s*(?:整改要求|整改建议)\s*[：:]\s*',
                # 备用模式：不带冒号的标题
                r'(?:^|\n)\s*(?:预防措施|防范措施|整改措施)\s*(?:\n|$)',
            ]
        }
    
    def extract_sections(self, text: str) -> Dict[str, str]:
        """从文本中提取章节内容"""
        sections = {}
        
        # 验证输入文本
        if not text or len(text.strip()) < 5:
            return sections
        
        # 预处理文本：统一换行符，去除多余空白
        text = self._preprocess_text(text)
        
        # 再次验证预处理后的文本
        if not text or len(text.strip()) < 5:
            return sections
        
        # 为每个章节类型查找内容
        for section_type, patterns in self.section_patterns.items():
            section_content = self._extract_section_content(text, patterns)
            if section_content:
                sections[section_type.value] = section_content
        
        # 如果没有找到标准章节，尝试智能分割
        if not sections:
            sections = self._intelligent_section_split(text)
        
        # 最后的保障：如果仍然没有章节，将整个文本作为事故经过
        if not sections and len(text.strip()) > 5:
            logger.warning("所有章节提取方法都失败，将整个文档作为事故经过章节")
            sections[SectionType.ACCIDENT_PROCESS.value] = text.strip()
        
        return sections
    
    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        if not text:
            return ""
        
        # 统一换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 去除多余的空白字符，但保留基本结构
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # 多个连续空行变为两个
        text = re.sub(r'[ \t]+', ' ', text)  # 多个空格/制表符变为一个空格
        
        # 去除首尾空白
        text = text.strip()
        
        return text
    
    def _extract_section_content(self, text: str, patterns: List[str]) -> Optional[str]:
        """根据模式提取章节内容"""
        for pattern in patterns:
            # 查找章节标题
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                start_pos = match.start()
                
                # 查找章节标题后的内容开始位置
                title_end = match.end()
                content_start = title_end
                
                # 跳过标题行后的换行符
                while content_start < len(text) and text[content_start] in '\n\r':
                    content_start += 1
                
                # 查找下一个章节标题的位置
                end_pos = len(text)
                remaining_text = text[content_start:]
                
                # 查找所有其他章节的开始位置
                next_section_positions = []
                for other_section_patterns in self.section_patterns.values():
                    for other_pattern in other_section_patterns:
                        other_match = re.search(other_pattern, remaining_text, re.IGNORECASE)
                        if other_match:
                            # 确保不是同一个匹配
                            other_abs_pos = content_start + other_match.start()
                            if other_abs_pos > start_pos + len(match.group()):
                                next_section_positions.append(other_abs_pos)
                
                # 找到最近的下一个章节位置
                if next_section_positions:
                    end_pos = min(next_section_positions)
                
                # 提取章节内容（不包括标题）
                section_text = text[content_start:end_pos].strip()
                
                # 清理章节内容
                section_text = self._clean_section_content(section_text)
                
                if len(section_text) > 10:  # 确保内容足够长
                    return section_text
        
        return None
    
    def _clean_section_content(self, content: str) -> str:
        """清理章节内容"""
        # 去除页眉页脚等无关内容
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not self._is_header_footer(line):
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _is_header_footer(self, line: str) -> bool:
        """判断是否为页眉页脚"""
        # 简单的页眉页脚识别规则
        if len(line) < 5:
            return True
        
        # 常见的页眉页脚模式
        header_footer_patterns = [
            r'^\d+$',  # 纯数字（页码）
            r'^第\s*\d+\s*页',  # 第X页
            r'^\d+\s*/\s*\d+$',  # X/Y格式页码
            r'^-\s*\d+\s*-$',  # -X-格式页码
        ]
        
        for pattern in header_footer_patterns:
            if re.match(pattern, line):
                return True
        
        return False
    
    def _intelligent_section_split(self, text: str) -> Dict[str, str]:
        """智能章节分割（当无法识别标准章节时使用）"""
        sections = {}
        
        # 确保文本不为空
        if not text or len(text.strip()) < 5:
            return sections
        
        text = text.strip()
        
        # 按段落分割文本
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # 如果没有段落分割，按句号分割
        if len(paragraphs) <= 1:
            sentences = [s.strip() for s in text.split('。') if s.strip()]
            if len(sentences) > 1:
                paragraphs = sentences
        
        # 如果仍然只有一个段落，按换行符分割
        if len(paragraphs) <= 1:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if len(lines) > 1:
                paragraphs = lines
        
        if len(paragraphs) >= 2:
            # 简单的启发式分割：前半部分作为事故经过，后半部分作为原因分析
            mid_point = len(paragraphs) // 2
            
            accident_process = '\n\n'.join(paragraphs[:mid_point])
            cause_analysis = '\n\n'.join(paragraphs[mid_point:])
            
            # 降低长度要求，使其更宽松
            if len(accident_process.strip()) > 10:
                sections[SectionType.ACCIDENT_PROCESS.value] = accident_process.strip()
            
            if len(cause_analysis.strip()) > 10:
                sections[SectionType.CAUSE_ANALYSIS.value] = cause_analysis.strip()
        
        # 如果分割后的内容太少或没有分割成功，将整个文本作为事故经过
        if not sections and len(text.strip()) > 5:
            sections[SectionType.ACCIDENT_PROCESS.value] = text.strip()
        
        return sections


class ExtractionService:
    """智能抽取服务"""
    
    def __init__(self):
        self.parser = DocumentParser()
        self.extractor = SectionExtractor()
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
    
    async def process_document(self, file: UploadFile) -> Tuple[str, DocumentSections]:
        """处理上传的文档"""
        # 验证文件类型
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in self.parser.supported_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file_extension}"
            )
        
        file_type = self.parser.supported_extensions[file_extension]
        
        # 生成唯一文件名
        document_id = str(uuid.uuid4())
        file_path = self.upload_dir / f"{document_id}{file_extension}"
        
        try:
            # 保存上传的文件
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            logger.info(f"文件保存成功: {file_path}")
            
            # 解析文档内容
            raw_text = self.parser.parse_document(str(file_path), file_type)
            logger.info(f"文档解析成功，提取文本长度: {len(raw_text)}")
            
            # 验证文档内容长度
            if len(raw_text.strip()) < 5:
                raise HTTPException(
                    status_code=400,
                    detail="文档内容过短或为空，请上传包含有效内容的文档"
                )
            
            # 提取章节
            sections = self.extractor.extract_sections(raw_text)
            logger.info(f"章节提取完成，找到 {len(sections)} 个章节")
            
            # 如果没有找到任何章节，将整个文档作为事故经过章节
            if not sections:
                logger.warning("未找到标准章节，将整个文档内容作为事故经过章节")
                sections = {SectionType.ACCIDENT_PROCESS.value: raw_text.strip()}
            
            # 创建文档章节对象
            try:
                document_sections = DocumentSections(sections=sections)
            except Exception as validation_error:
                logger.error(f"章节验证失败: {validation_error}")
                raise HTTPException(
                    status_code=400,
                    detail=f"文档章节验证失败: {str(validation_error)}"
                )
            
            return document_id, document_sections
            
        except HTTPException:
            # 重新抛出HTTP异常
            if file_path.exists():
                file_path.unlink()
            raise
        except Exception as e:
            # 清理临时文件
            if file_path.exists():
                file_path.unlink()
            logger.error(f"文档处理失败: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"文档处理失败: {str(e)}"
            )
    
    async def extract_and_validate_event_chains(
        self, 
        document_sections: DocumentSections,
        apply_validation: bool = True
    ) -> Tuple[List[EventChainCreate], Dict[str, any]]:
        """
        从文档章节中提取并验证事件链
        
        Args:
            document_sections: 文档章节
            apply_validation: 是否应用验证和归一化
            
        Returns:
            (事件链列表, 处理统计信息)
        """
        # 合并所有章节文本
        combined_text = ""
        for section_name, section_content in document_sections.sections.items():
            combined_text += f"\n{section_name}:\n{section_content}\n"
        
        # 使用LLM服务提取事件链
        logger.info("开始LLM事件链提取...")
        raw_event_chains = await llm_service.extract_event_chains(combined_text.strip())
        logger.info(f"LLM提取完成，获得 {len(raw_event_chains)} 个原始事件链")
        
        if not apply_validation:
            return raw_event_chains, {
                "raw_chains": len(raw_event_chains),
                "valid_chains": len(raw_event_chains),
                "filtered_chains": 0,
                "validation_applied": False
            }
        
        # 应用验证和归一化
        logger.info("开始事件链验证和归一化...")
        valid_chains, validation_results = validation_service.filter_valid_chains(
            raw_event_chains, 
            apply_normalization=True
        )
        
        # 获取验证统计信息
        validation_stats = validation_service.get_validation_statistics(validation_results)
        
        processing_stats = {
            "raw_chains": len(raw_event_chains),
            "valid_chains": len(valid_chains),
            "filtered_chains": len(raw_event_chains) - len(valid_chains),
            "validation_applied": True,
            "validation_rate": validation_stats["validation_rate"],
            "avg_confidence": validation_stats["avg_confidence"],
            "common_errors": validation_stats["common_errors"]
        }
        
        logger.info(f"验证完成: {len(valid_chains)}/{len(raw_event_chains)} 个事件链通过验证")
        
        return valid_chains, processing_stats
    
    async def process_document_with_extraction(
        self, 
        file: UploadFile,
        apply_validation: bool = True
    ) -> Tuple[str, DocumentSections, List[EventChainCreate], Dict[str, any]]:
        """
        完整的文档处理流程：上传 -> 解析 -> 章节提取 -> 事件链提取 -> 验证
        
        Args:
            file: 上传的文件
            apply_validation: 是否应用验证和归一化
            
        Returns:
            (文档ID, 文档章节, 事件链列表, 处理统计信息)
        """
        # 处理文档并提取章节
        document_id, document_sections = await self.process_document(file)
        
        # 提取并验证事件链
        event_chains, processing_stats = await self.extract_and_validate_event_chains(
            document_sections, 
            apply_validation
        )
        
        return document_id, document_sections, event_chains, processing_stats
    
    def get_document_path(self, document_id: str, file_extension: str) -> Path:
        """获取文档路径"""
        return self.upload_dir / f"{document_id}{file_extension}"
    
    def cleanup_document(self, document_id: str, file_extension: str) -> bool:
        """清理文档文件"""
        try:
            file_path = self.get_document_path(document_id, file_extension)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"文档文件已清理: {file_path}")
                return True
        except Exception as e:
            logger.error(f"清理文档文件失败: {e}")
        
        return False
    
    def validate_sections(self, sections: Dict[str, str]) -> List[str]:
        """验证章节内容"""
        errors = []
        
        # 检查必需章节
        required_sections = [SectionType.ACCIDENT_PROCESS.value, SectionType.CAUSE_ANALYSIS.value]
        for section in required_sections:
            if section not in sections:
                errors.append(f"缺少必需章节: {section}")
            elif len(sections[section].strip()) < 20:  # 降低最小长度要求
                errors.append(f"章节内容过短: {section}")
        
        return errors
    
    async def analyze_document_quality(self, document_sections: DocumentSections) -> Dict[str, any]:
        """
        分析文档质量
        
        Args:
            document_sections: 文档章节
            
        Returns:
            质量分析结果
        """
        # 合并所有章节文本
        combined_text = ""
        for section_name, section_content in document_sections.sections.items():
            combined_text += f"{section_content}\n"
        
        # 使用LLM服务分析文本质量
        quality_analysis = await llm_service.analyze_text_quality(combined_text.strip())
        
        # 获取术语标准化建议
        terminology_suggestions = validation_service.get_terminology_suggestions(combined_text)
        
        return {
            "text_quality": quality_analysis,
            "terminology_suggestions": terminology_suggestions,
            "section_count": len(document_sections.sections),
            "total_length": len(combined_text),
            "sections": list(document_sections.sections.keys())
        }


# 全局服务实例
extraction_service = ExtractionService()