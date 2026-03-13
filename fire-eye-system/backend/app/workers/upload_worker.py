"""
文件上传后台工作器
处理文件上传、文本提取和分析任务
"""

import logging
import asyncio
import os
from pathlib import Path
from typing import Dict, Any, Optional

from app.services.task_manager import task_manager, TaskType, TaskStatus, TaskResult
from app.services.extraction_service import extraction_service
from app.workers.analysis_worker import process_analyze_task
from app.core.config import settings

logger = logging.getLogger(__name__)


async def extract_text_from_file(file_path: str) -> str:
    """
    从文件中提取文本内容
    
    Args:
        file_path: 文件路径
        
    Returns:
        提取的文本内容
        
    Raises:
        ValueError: 不支持的文件类型
        IOError: 文件读取失败
    """
    file_ext = Path(file_path).suffix.lower()
    
    try:
        if file_ext == '.txt':
            # 读取纯文本文件
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        elif file_ext == '.pdf':
            # 提取 PDF 文本
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    return text
            except ImportError:
                logger.warning("PyPDF2 not installed, falling back to basic extraction")
                # 如果没有 PyPDF2，尝试使用 extraction_service
                return await extraction_service.extract_text_from_pdf(file_path)
        
        elif file_ext in ['.doc', '.docx']:
            # 提取 Word 文档文本
            try:
                import docx
                doc = docx.Document(file_path)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                return text
            except ImportError:
                logger.warning("python-docx not installed, falling back to basic extraction")
                # 如果没有 python-docx，尝试使用 extraction_service
                return await extraction_service.extract_text_from_docx(file_path)
        
        else:
            raise ValueError(f"不支持的文件类型: {file_ext}")
    
    except Exception as e:
        logger.error(f"Failed to extract text from {file_path}: {e}")
        raise IOError(f"文件读取失败: {str(e)}")


async def process_upload_task(
    task_id: str,
    file_path: str,
    document_id: str,
    metadata: Dict[str, Any] = None,
    delete_after_processing: bool = True
) -> None:
    """
    处理文件上传任务
    
    Args:
        task_id: 任务 ID
        file_path: 上传的文件路径
        document_id: 文档 ID
        metadata: 任务元数据
        delete_after_processing: 处理完成后是否删除文件
    """
    try:
        logger.info(f"Starting upload task {task_id} for file {file_path}")
        
        # 更新进度：开始处理
        await task_manager.update_task_progress(
            task_id=task_id,
            progress=10,
            status=TaskStatus.PROCESSING
        )
        
        # 步骤 1: 验证文件存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 步骤 2: 提取文本内容
        logger.info(f"Task {task_id}: Extracting text from file")
        text = await extract_text_from_file(file_path)
        
        if not text or len(text.strip()) == 0:
            raise ValueError("文件内容为空或无法提取文本")
        
        # 更新进度：文本提取完成
        await task_manager.update_task_progress(
            task_id=task_id,
            progress=30,
            status=TaskStatus.PROCESSING
        )
        
        # 步骤 3: 调用分析工作器处理文本
        logger.info(f"Task {task_id}: Starting text analysis")
        
        # 创建分析子任务的元数据
        analysis_metadata = {
            "document_id": document_id,
            "file_path": file_path,
            "parent_task_id": task_id
        }
        if metadata:
            analysis_metadata.update(metadata)
        
        # 直接调用分析函数（不创建新任务）
        # 使用临时任务 ID 来跟踪分析进度
        analysis_task_id = f"{task_id}_analysis"
        
        # 创建临时分析任务 - 手动创建以使用自定义 ID
        from app.services.task_manager import Task
        analysis_task = Task(
            task_id=analysis_task_id,
            task_type=TaskType.ANALYZE,
            status=TaskStatus.PENDING,
            progress=0,
            estimated_time=60,
            metadata=analysis_metadata
        )
        await task_manager._save_task(analysis_task)
        
        # 执行分析
        await process_analyze_task(analysis_task_id, text, analysis_metadata)
        
        # 获取分析结果
        analysis_task = await task_manager.get_task_status(analysis_task_id)
        
        if analysis_task and analysis_task.status == TaskStatus.COMPLETED:
            # 分析成功
            result = TaskResult(
                event_chains=analysis_task.result.event_chains if analysis_task.result else [],
                entities_count=analysis_task.result.entities_count if analysis_task.result else 0,
                relationships_count=analysis_task.result.relationships_count if analysis_task.result else 0,
                document_id=document_id,
                message=f"文件上传并分析成功: {Path(file_path).name}"
            )
            
            # 完成任务
            await task_manager.complete_task(task_id=task_id, result=result)
            
            logger.info(f"Task {task_id} completed successfully")
        else:
            # 分析失败
            error_msg = analysis_task.error if analysis_task else "分析任务未完成"
            raise Exception(f"文本分析失败: {error_msg}")
        
        # 步骤 4: 清理文件（如果配置为删除）
        if delete_after_processing:
            try:
                os.remove(file_path)
                logger.info(f"Task {task_id}: Deleted file {file_path}")
            except Exception as e:
                logger.warning(f"Task {task_id}: Failed to delete file {file_path}: {e}")
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)
        
        # 标记任务失败
        await task_manager.fail_task(
            task_id=task_id,
            error=f"文件处理失败: {str(e)}"
        )
        
        # 尝试清理文件
        if delete_after_processing and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Task {task_id}: Cleaned up file after failure")
            except Exception as cleanup_error:
                logger.warning(f"Task {task_id}: Failed to cleanup file: {cleanup_error}")


def start_upload_task(
    task_id: str,
    file_path: str,
    document_id: str,
    metadata: Dict[str, Any] = None,
    delete_after_processing: bool = True
) -> asyncio.Task:
    """
    启动文件上传任务（非阻塞）
    
    Args:
        task_id: 任务 ID
        file_path: 上传的文件路径
        document_id: 文档 ID
        metadata: 任务元数据
        delete_after_processing: 处理完成后是否删除文件
        
    Returns:
        asyncio.Task 对象
    """
    return asyncio.create_task(
        process_upload_task(task_id, file_path, document_id, metadata, delete_after_processing)
    )
