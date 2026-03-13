"""
校验对齐服务测试
"""

import pytest
import json
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

from app.services.validation_service import ValidationService, validation_service, SimpleValidationResult
from app.schemas.event_chain import EventChainCreate, RelationType


class TestValidationService:
    """校验对齐服务测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.service = ValidationService()
        # 设置测试用的术语映射
        self.service.terminology_mapping = {
            "电瓶车": "电动自行车",
            "电单车": "电动自行车",
            "电池": "蓄电池",
            "起火": "火灾",
            "短路": "电气短路"
        }
    
    def test_initialization(self):
        """测试服务初始化"""
        assert self.service.confidence_threshold == 0.6
        assert self.service.min_text_length == 2
        assert self.service.max_text_length == 100
        assert isinstance(self.service.terminology_mapping, dict)
    
    def test_normalize_terminology(self):
        """测试术语归一化"""
        # 测试基本归一化
        text = "电瓶车充电时发生短路起火"
        normalized = self.service.normalize_terminology(text)
        expected = "电动自行车充电时发生电气短路火灾"
        assert normalized == expected
        
        # 测试空文本
        assert self.service.normalize_terminology("") == ""
        assert self.service.normalize_terminology(None) is None
        
        # 测试无需归一化的文本
        text = "正常文本内容"
        assert self.service.normalize_terminology(text) == text
    
    def test_validate_event_chain_valid(self):
        """测试验证有效事件链"""
        chain = EventChainCreate(
            source="电线老化",
            relation=RelationType.CAUSES,
            target="绝缘层破损",
            confidence=0.8,
            context="长期使用导致老化"
        )
        
        result = self.service.validate_event_chain(chain)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.confidence_score == 0.8
    
    def test_validate_event_chain_low_confidence(self):
        """测试验证低置信度事件链"""
        chain = EventChainCreate(
            source="天气炎热",
            relation=RelationType.CAUSES,
            target="火灾发生",
            confidence=0.3,  # 低于阈值0.6
            context="天气因素"
        )
        
        result = self.service.validate_event_chain(chain)
        
        assert result.is_valid is False
        assert any("置信度" in error for error in result.errors)
    
    def test_validate_event_chain_empty_source(self):
        """测试验证极短源事件"""
        chain = EventChainCreate(
            source="a",  # 极短但非空
            relation=RelationType.CAUSES,
            target="设备损坏",
            confidence=0.8,
            context="测试极短源事件"
        )
        
        result = self.service.validate_event_chain(chain)
        
        assert result.is_valid is False
        assert any("源事件长度不能少于" in error for error in result.errors)
    
    def test_validate_event_chain_same_source_target(self):
        """测试验证源事件和目标事件相同"""
        chain = EventChainCreate(
            source="电路短路",
            relation=RelationType.CAUSES,
            target="电路短路",
            confidence=0.8,
            context="循环引用测试"
        )
        
        result = self.service.validate_event_chain(chain)
        
        assert result.is_valid is False
        assert any("源事件和目标事件不能相同" in error for error in result.errors)
    
    def test_validate_event_chain_long_text(self):
        """测试验证过长文本"""
        long_text = "这是一个非常长的文本" * 20  # 超过100字符
        
        chain = EventChainCreate(
            source=long_text,
            relation=RelationType.CAUSES,
            target="目标事件",
            confidence=0.8,
            context="测试长文本"
        )
        
        result = self.service.validate_event_chain(chain)
        
        # 应该有警告但仍然有效（如果其他条件满足）
        assert len(result.warnings) > 0
        assert any("长度超过" in warning for warning in result.warnings)
    
    def test_validate_event_chains_batch(self):
        """测试批量验证事件链"""
        chains = [
            EventChainCreate(
                source="有效源事件",
                relation=RelationType.CAUSES,
                target="有效目标事件",
                confidence=0.8,
                context="有效事件链"
            ),
            EventChainCreate(
                source="a",  # 极短但非空
                relation=RelationType.CAUSES,
                target="无效目标事件",
                confidence=0.8,
                context="无效事件链"
            )
        ]
        
        results = self.service.validate_event_chains(chains)
        
        assert len(results) == 2
        assert results[0].is_valid is True
        assert results[1].is_valid is False
    
    def test_filter_valid_chains(self):
        """测试过滤有效事件链"""
        chains = [
            EventChainCreate(
                source="电瓶车充电器过热",  # 会被归一化
                relation=RelationType.CAUSES,
                target="引燃可燃物",
                confidence=0.8,
                context="有效事件链"
            ),
            EventChainCreate(
                source="天气因素",
                relation=RelationType.CAUSES,
                target="火灾",
                confidence=0.3,  # 低置信度，会被过滤
                context="无效事件链"
            )
        ]
        
        valid_chains, validation_results = self.service.filter_valid_chains(
            chains, 
            apply_normalization=True
        )
        
        assert len(valid_chains) == 1
        assert len(validation_results) == 2
        assert "电动自行车" in valid_chains[0].source  # 验证归一化
    
    def test_normalize_event_chain(self):
        """测试事件链归一化"""
        chain = EventChainCreate(
            source="电瓶车电池过热",
            relation=RelationType.CAUSES,
            target="起火燃烧",
            confidence=0.8,
            context="电单车充电故障"
        )
        
        normalized_chain = self.service._normalize_event_chain(chain)
        
        assert "电动自行车" in normalized_chain.source
        assert "蓄电池" in normalized_chain.source
        assert "火灾" in normalized_chain.target
        assert "电动自行车" in normalized_chain.context
    
    def test_extract_time_info(self):
        """测试时间信息提取"""
        # 测试日期时间提取
        text = "2023年3月15日上午10:30发生故障"
        time_info = self.service._extract_time_info(text)
        
        assert time_info is not None
        assert time_info['year'] == 2023
        assert time_info['month'] == 3
        assert time_info['day'] == 15
        assert time_info['hour'] == 10
        assert time_info['minute'] == 30
        assert time_info['period'] == 'morning'
        
        # 测试无时间信息的文本
        text = "普通文本内容"
        time_info = self.service._extract_time_info(text)
        assert time_info is None or len(time_info) == 0
    
    def test_validate_time_sequence(self):
        """测试时间序列验证"""
        # 正确的时间顺序
        source_time = {'hour': 10, 'minute': 30, 'period': 'morning'}
        target_time = {'hour': 10, 'minute': 35, 'period': 'morning'}
        
        assert self.service._validate_time_sequence(source_time, target_time) is True
        
        # 错误的时间顺序
        source_time = {'hour': 15, 'minute': 30, 'period': 'afternoon'}
        target_time = {'hour': 14, 'minute': 30, 'period': 'afternoon'}
        
        assert self.service._validate_time_sequence(source_time, target_time) is False
    
    def test_get_validation_statistics(self):
        """测试获取验证统计信息"""
        results = [
            SimpleValidationResult(True, [], [], 0.8),
            SimpleValidationResult(False, ["错误1"], [], 0.5),
            SimpleValidationResult(False, ["错误1", "错误2"], [], 0.3),
            SimpleValidationResult(True, [], ["警告1"], 0.9)
        ]
        
        stats = self.service.get_validation_statistics(results)
        
        assert stats['total_chains'] == 4
        assert stats['valid_chains'] == 2
        assert stats['invalid_chains'] == 2
        assert stats['validation_rate'] == 0.5
        assert stats['avg_confidence'] == 0.625
        assert len(stats['common_errors']) > 0
    
    def test_update_confidence_threshold(self):
        """测试更新置信度阈值"""
        # 有效阈值
        self.service.update_confidence_threshold(0.8)
        assert self.service.confidence_threshold == 0.8
        
        # 无效阈值
        with pytest.raises(ValueError):
            self.service.update_confidence_threshold(1.5)
        
        with pytest.raises(ValueError):
            self.service.update_confidence_threshold(-0.1)
    
    def test_add_terminology_mapping(self):
        """测试添加术语映射"""
        original_count = len(self.service.terminology_mapping)
        
        self.service.add_terminology_mapping("新术语", "标准术语")
        
        assert len(self.service.terminology_mapping) == original_count + 1
        assert self.service.terminology_mapping["新术语"] == "标准术语"
    
    def test_get_terminology_suggestions(self):
        """测试获取术语标准化建议"""
        text = "电瓶车充电时电池过热导致起火"
        suggestions = self.service.get_terminology_suggestions(text)
        
        assert len(suggestions) > 0
        assert any("电瓶车" in suggestion for suggestion in suggestions)
        assert any("电池" in suggestion for suggestion in suggestions)
        assert any("起火" in suggestion for suggestion in suggestions)
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"test_category": {"原术语": "标准术语"}}')
    @patch('pathlib.Path.exists', return_value=True)
    def test_load_terminology_mapping(self, mock_exists, mock_file):
        """测试加载术语映射配置"""
        service = ValidationService()
        
        # 验证映射已加载
        assert "原术语" in service.terminology_mapping
        assert service.terminology_mapping["原术语"] == "标准术语"
    
    @patch('pathlib.Path.exists', return_value=False)
    def test_load_terminology_mapping_file_not_exists(self, mock_exists):
        """测试术语映射文件不存在的情况"""
        service = ValidationService()
        
        # 应该不会抛出异常，只是映射为空
        assert isinstance(service.terminology_mapping, dict)


class TestGlobalValidationService:
    """全局验证服务实例测试"""
    
    def test_validation_service_instance(self):
        """测试全局验证服务实例"""
        assert validation_service is not None
        assert isinstance(validation_service, ValidationService)
        assert hasattr(validation_service, 'terminology_mapping')
        assert hasattr(validation_service, 'confidence_threshold')