"""
校验对齐服务
实现术语归一化和逻辑校验功能
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

from app.schemas.event_chain import EventChainCreate, EventChain
from app.schemas.validation import ValidationStatus, TermMapping, TermCategory

logger = logging.getLogger(__name__)


class SimpleValidationResult:
    """简单验证结果类"""
    
    def __init__(self, is_valid: bool, errors: List[str], warnings: List[str], confidence_score: float):
        self.is_valid = is_valid
        self.errors = errors
        self.warnings = warnings
        self.confidence_score = confidence_score


class ValidationService:
    """校验对齐服务类"""
    
    def __init__(self):
        """初始化校验服务"""
        self.terminology_mapping: Dict[str, str] = {}
        self.confidence_threshold = 0.6
        self.min_text_length = 2
        self.max_text_length = 100
        
        # 加载术语映射
        self._load_terminology_mapping()
        
        # 时间模式匹配
        self.time_patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{1,2})月(\d{1,2})日',
            r'(\d{1,2}):(\d{2})',
            r'(\d{1,2})时(\d{1,2})分',
            r'上午|下午|凌晨|中午|傍晚|晚上'
        ]
        
        logger.info("校验对齐服务初始化完成")
    
    def _load_terminology_mapping(self) -> None:
        """加载术语映射配置"""
        try:
            mapping_file = Path(__file__).parent.parent / "data" / "terminology_mapping.json"
            
            if not mapping_file.exists():
                logger.warning(f"术语映射文件不存在: {mapping_file}")
                return
            
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mapping_data = json.load(f)
            
            # 合并所有类别的映射
            for category, mappings in mapping_data.items():
                self.terminology_mapping.update(mappings)
            
            logger.info(f"成功加载 {len(self.terminology_mapping)} 个术语映射规则")
            
        except Exception as e:
            logger.error(f"加载术语映射失败: {e}")
    
    def normalize_terminology(self, text: str) -> str:
        """
        术语归一化处理
        
        Args:
            text: 待处理的文本
            
        Returns:
            归一化后的文本
        """
        if not text or not isinstance(text, str):
            return text
        
        normalized_text = text.strip()
        
        # 应用术语映射
        for original_term, standard_term in self.terminology_mapping.items():
            if original_term in normalized_text:
                normalized_text = normalized_text.replace(original_term, standard_term)
        
        return normalized_text
    
    def validate_event_chain(self, event_chain: EventChainCreate) -> SimpleValidationResult:
        """
        验证单个事件链
        
        Args:
            event_chain: 待验证的事件链
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        # 1. 基础字段验证
        if not event_chain.source or not event_chain.source.strip():
            errors.append("源事件不能为空")
        elif len(event_chain.source.strip()) < self.min_text_length:
            errors.append(f"源事件长度不能少于{self.min_text_length}个字符")
        elif len(event_chain.source) > self.max_text_length:
            warnings.append(f"源事件长度超过{self.max_text_length}个字符，建议简化")
        
        if not event_chain.target or not event_chain.target.strip():
            errors.append("目标事件不能为空")
        elif len(event_chain.target.strip()) < self.min_text_length:
            errors.append(f"目标事件长度不能少于{self.min_text_length}个字符")
        elif len(event_chain.target) > self.max_text_length:
            warnings.append(f"目标事件长度超过{self.max_text_length}个字符，建议简化")
        
        # 2. 置信度验证
        if event_chain.confidence < self.confidence_threshold:
            errors.append(f"置信度 {event_chain.confidence:.2f} 低于阈值 {self.confidence_threshold}")
        
        if event_chain.confidence > 1.0:
            errors.append(f"置信度 {event_chain.confidence:.2f} 不能大于1.0")
        
        # 3. 逻辑一致性验证
        if event_chain.source.strip() == event_chain.target.strip():
            errors.append("源事件和目标事件不能相同")
        
        # 4. 时间逻辑验证（如果包含时间信息）
        source_time = self._extract_time_info(event_chain.source)
        target_time = self._extract_time_info(event_chain.target)
        
        if source_time and target_time:
            if not self._validate_time_sequence(source_time, target_time):
                warnings.append("时间顺序可能不合理：源事件时间晚于目标事件时间")
        
        # 5. 关系类型验证
        if not event_chain.relation:
            errors.append("关系类型不能为空")
        
        # 6. 上下文验证
        if event_chain.context and len(event_chain.context) > 200:
            warnings.append("上下文信息过长，建议简化")
        
        return SimpleValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            confidence_score=event_chain.confidence
        )
    
    def validate_event_chains(self, event_chains: List[EventChainCreate]) -> List[SimpleValidationResult]:
        """
        批量验证事件链
        
        Args:
            event_chains: 待验证的事件链列表
            
        Returns:
            验证结果列表
        """
        results = []
        
        for i, event_chain in enumerate(event_chains):
            try:
                result = self.validate_event_chain(event_chain)
                results.append(result)
            except Exception as e:
                logger.error(f"验证第 {i+1} 个事件链时出错: {e}")
                results.append(SimpleValidationResult(
                    is_valid=False,
                    errors=[f"验证过程出错: {str(e)}"],
                    warnings=[],
                    confidence_score=0.0
                ))
        
        return results
    
    def filter_valid_chains(
        self, 
        event_chains: List[EventChainCreate],
        apply_normalization: bool = True
    ) -> Tuple[List[EventChainCreate], List[SimpleValidationResult]]:
        """
        过滤并返回有效的事件链
        
        Args:
            event_chains: 原始事件链列表
            apply_normalization: 是否应用术语归一化
            
        Returns:
            (有效事件链列表, 验证结果列表)
        """
        valid_chains = []
        validation_results = []
        
        for event_chain in event_chains:
            # 应用术语归一化
            if apply_normalization:
                normalized_chain = self._normalize_event_chain(event_chain)
            else:
                normalized_chain = event_chain
            
            # 验证事件链
            validation_result = self.validate_event_chain(normalized_chain)
            validation_results.append(validation_result)
            
            # 只保留有效的事件链
            if validation_result.is_valid:
                valid_chains.append(normalized_chain)
            else:
                logger.info(f"过滤无效事件链: {event_chain.source} -> {event_chain.target}, "
                           f"错误: {validation_result.errors}")
        
        logger.info(f"事件链过滤完成: {len(valid_chains)}/{len(event_chains)} 个有效")
        
        return valid_chains, validation_results
    
    def _normalize_event_chain(self, event_chain: EventChainCreate) -> EventChainCreate:
        """
        对事件链应用术语归一化
        
        Args:
            event_chain: 原始事件链
            
        Returns:
            归一化后的事件链
        """
        return EventChainCreate(
            source=self.normalize_terminology(event_chain.source),
            relation=event_chain.relation,
            target=self.normalize_terminology(event_chain.target),
            confidence=event_chain.confidence,
            context=self.normalize_terminology(event_chain.context) if event_chain.context else None
        )
    
    def _extract_time_info(self, text: str) -> Optional[Dict[str, Any]]:
        """
        从文本中提取时间信息
        
        Args:
            text: 文本内容
            
        Returns:
            时间信息字典或None
        """
        if not text:
            return None
        
        time_info = {}
        
        # 匹配日期
        date_pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
        date_match = re.search(date_pattern, text)
        if date_match:
            time_info['year'] = int(date_match.group(1))
            time_info['month'] = int(date_match.group(2))
            time_info['day'] = int(date_match.group(3))
        
        # 匹配时间
        time_pattern = r'(\d{1,2}):(\d{2})'
        time_match = re.search(time_pattern, text)
        if time_match:
            time_info['hour'] = int(time_match.group(1))
            time_info['minute'] = int(time_match.group(2))
        
        # 匹配中文时间
        chinese_time_pattern = r'(\d{1,2})时(\d{1,2})分'
        chinese_time_match = re.search(chinese_time_pattern, text)
        if chinese_time_match:
            time_info['hour'] = int(chinese_time_match.group(1))
            time_info['minute'] = int(chinese_time_match.group(2))
        
        # 匹配时段
        if '上午' in text:
            time_info['period'] = 'morning'
        elif '下午' in text:
            time_info['period'] = 'afternoon'
        elif '凌晨' in text:
            time_info['period'] = 'early_morning'
        elif '晚上' in text:
            time_info['period'] = 'evening'
        
        return time_info if time_info else None
    
    def _validate_time_sequence(self, source_time: Dict[str, Any], target_time: Dict[str, Any]) -> bool:
        """
        验证时间序列的合理性
        
        Args:
            source_time: 源事件时间信息
            target_time: 目标事件时间信息
            
        Returns:
            时间序列是否合理
        """
        try:
            # 构建时间对象进行比较
            source_dt = self._build_datetime(source_time)
            target_dt = self._build_datetime(target_time)
            
            if source_dt and target_dt:
                return source_dt <= target_dt
            
            # 如果无法构建完整时间，进行简单比较
            if 'hour' in source_time and 'hour' in target_time:
                source_hour = source_time['hour']
                target_hour = target_time['hour']
                
                # 考虑时段信息
                if 'period' in source_time and 'period' in target_time:
                    period_order = {'early_morning': 0, 'morning': 1, 'afternoon': 2, 'evening': 3}
                    source_period = period_order.get(source_time['period'], 1)
                    target_period = period_order.get(target_time['period'], 1)
                    
                    if source_period != target_period:
                        return source_period <= target_period
                
                return source_hour <= target_hour
            
            return True  # 无法确定时返回True，避免误判
            
        except Exception as e:
            logger.warning(f"时间序列验证出错: {e}")
            return True
    
    def _build_datetime(self, time_info: Dict[str, Any]) -> Optional[datetime]:
        """
        根据时间信息构建datetime对象
        
        Args:
            time_info: 时间信息字典
            
        Returns:
            datetime对象或None
        """
        try:
            year = time_info.get('year', datetime.now().year)
            month = time_info.get('month', 1)
            day = time_info.get('day', 1)
            hour = time_info.get('hour', 0)
            minute = time_info.get('minute', 0)
            
            return datetime(year, month, day, hour, minute)
        except (ValueError, TypeError):
            return None
    
    def get_validation_statistics(self, validation_results: List[SimpleValidationResult]) -> Dict[str, Any]:
        """
        获取验证统计信息
        
        Args:
            validation_results: 验证结果列表
            
        Returns:
            统计信息字典
        """
        if not validation_results:
            return {
                "total_chains": 0,
                "valid_chains": 0,
                "invalid_chains": 0,
                "validation_rate": 0.0,
                "avg_confidence": 0.0,
                "common_errors": []
            }
        
        total_chains = len(validation_results)
        valid_chains = sum(1 for result in validation_results if result.is_valid)
        invalid_chains = total_chains - valid_chains
        
        # 计算平均置信度
        avg_confidence = sum(result.confidence_score for result in validation_results) / total_chains
        
        # 统计常见错误
        error_counts = {}
        for result in validation_results:
            for error in result.errors:
                error_counts[error] = error_counts.get(error, 0) + 1
        
        common_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_chains": total_chains,
            "valid_chains": valid_chains,
            "invalid_chains": invalid_chains,
            "validation_rate": valid_chains / total_chains if total_chains > 0 else 0.0,
            "avg_confidence": avg_confidence,
            "common_errors": common_errors
        }
    
    def update_confidence_threshold(self, threshold: float) -> None:
        """
        更新置信度阈值
        
        Args:
            threshold: 新的置信度阈值
        """
        if 0.0 <= threshold <= 1.0:
            self.confidence_threshold = threshold
            logger.info(f"置信度阈值已更新为: {threshold}")
        else:
            raise ValueError("置信度阈值必须在0.0到1.0之间")
    
    def add_terminology_mapping(self, original_term: str, standard_term: str) -> None:
        """
        添加术语映射规则
        
        Args:
            original_term: 原始术语
            standard_term: 标准术语
        """
        self.terminology_mapping[original_term] = standard_term
        logger.info(f"添加术语映射: {original_term} -> {standard_term}")
    
    def get_terminology_suggestions(self, text: str) -> List[str]:
        """
        获取术语标准化建议
        
        Args:
            text: 待分析的文本
            
        Returns:
            建议列表
        """
        suggestions = []
        
        for original_term, standard_term in self.terminology_mapping.items():
            if original_term in text and original_term != standard_term:
                suggestions.append(f"建议将 '{original_term}' 标准化为 '{standard_term}'")
        
        return suggestions


# 全局验证服务实例
validation_service = ValidationService()