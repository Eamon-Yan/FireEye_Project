"""
数据模型测试
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas import (
    EventChain,
    EventChainCreate,
    RelationType,
    FireEventNode,
    EventType,
    Node,
    Relationship,
    RelationshipType,
    ExtractionResult,
    ValidationResult,
    PredictionRequest,
    ScenarioType,
    Document,
    DocumentStatus,
    FileType,
    User,
    UserRole,
    UserStatus,
)


class TestEventChainModels:
    """事件链模型测试"""
    
    def test_event_chain_create_valid(self):
        """测试创建有效事件链"""
        chain_data = {
            "source": "电线老化",
            "relation": RelationType.CAUSES,
            "target": "短路打火",
            "confidence": 0.85,
            "context": "老旧建筑电气线路"
        }
        
        chain = EventChainCreate(**chain_data)
        assert chain.source == "电线老化"
        assert chain.relation == RelationType.CAUSES
        assert chain.target == "短路打火"
        assert chain.confidence == 0.85
        assert chain.context == "老旧建筑电气线路"
    
    def test_event_chain_invalid_confidence(self):
        """测试无效置信度"""
        chain_data = {
            "source": "电线老化",
            "relation": RelationType.CAUSES,
            "target": "短路打火",
            "confidence": 1.5,  # 无效值
            "context": "测试"
        }
        
        with pytest.raises(ValidationError):
            EventChainCreate(**chain_data)
    
    def test_event_chain_empty_source(self):
        """测试空源事件"""
        chain_data = {
            "source": "",  # 空值
            "relation": RelationType.CAUSES,
            "target": "短路打火",
            "confidence": 0.85,
            "context": "测试"
        }
        
        with pytest.raises(ValidationError):
            EventChainCreate(**chain_data)


class TestGraphModels:
    """图数据模型测试"""
    
    def test_fire_event_node_valid(self):
        """测试创建有效火灾事件节点"""
        node_data = {
            "id": "event_001",
            "event_type": EventType.CAUSE,
            "description": "电线老化导致短路",
            "standard_term": "电气线路老化",
            "category": "电气火灾",
            "severity_level": 5,
            "frequency": 10
        }
        
        node = FireEventNode(**node_data)
        assert node.id == "event_001"
        assert node.event_type == EventType.CAUSE
        assert node.severity_level == 5
    
    def test_fire_event_node_invalid_severity(self):
        """测试无效严重程度"""
        node_data = {
            "id": "event_001",
            "event_type": EventType.CAUSE,
            "description": "电线老化导致短路",
            "standard_term": "电气线路老化",
            "category": "电气火灾",
            "severity_level": 15,  # 超出范围
            "frequency": 10
        }
        
        with pytest.raises(ValidationError):
            FireEventNode(**node_data)
    
    def test_relationship_valid(self):
        """测试创建有效关系"""
        rel_data = {
            "id": "rel_001",
            "type": RelationshipType.CAUSES,
            "start_node": "event_001",
            "end_node": "event_002",
            "properties": {"confidence": 0.8},
            "weight": 0.8
        }
        
        rel = Relationship(**rel_data)
        assert rel.type == RelationshipType.CAUSES
        assert rel.weight == 0.8


class TestDocumentModels:
    """文档模型测试"""
    
    def test_document_valid(self):
        """测试创建有效文档"""
        doc_data = {
            "document_id": "doc_001",
            "title": "火灾调查报告",
            "file_path": "/uploads/report.pdf",
            "file_type": FileType.PDF,
            "file_size": 1024000,
            "upload_time": datetime.now(),
            "processing_status": DocumentStatus.UPLOADED
        }
        
        doc = Document(**doc_data)
        assert doc.title == "火灾调查报告"
        assert doc.file_type == FileType.PDF
        assert doc.processing_status == DocumentStatus.UPLOADED
    
    def test_document_invalid_file_size(self):
        """测试无效文件大小"""
        doc_data = {
            "document_id": "doc_001",
            "title": "火灾调查报告",
            "file_path": "/uploads/report.pdf",
            "file_type": FileType.PDF,
            "file_size": -1000,  # 负数
            "upload_time": datetime.now(),
            "processing_status": DocumentStatus.UPLOADED
        }
        
        with pytest.raises(ValidationError):
            Document(**doc_data)


class TestUserModels:
    """用户模型测试"""
    
    def test_user_valid(self):
        """测试创建有效用户"""
        user_data = {
            "user_id": "user_001",
            "username": "test_user",
            "email": "test@example.com",
            "full_name": "测试用户",
            "role": UserRole.ANALYST,
            "status": UserStatus.ACTIVE
        }
        
        user = User(**user_data)
        assert user.username == "test_user"
        assert user.role == UserRole.ANALYST
        assert user.status == UserStatus.ACTIVE
    
    def test_user_invalid_email(self):
        """测试无效邮箱"""
        user_data = {
            "user_id": "user_001",
            "username": "test_user",
            "email": "invalid-email",  # 无效邮箱格式
            "full_name": "测试用户",
            "role": UserRole.ANALYST,
            "status": UserStatus.ACTIVE
        }
        
        with pytest.raises(ValidationError):
            User(**user_data)


class TestValidationModels:
    """验证模型测试"""
    
    def test_extraction_result_valid(self):
        """测试创建有效抽取结果"""
        # 创建事件链
        chain = EventChain(
            source="电线老化",
            relation=RelationType.CAUSES,
            target="短路打火",
            confidence=0.85,
            context="测试上下文"
        )
        
        result_data = {
            "document_id": "doc_001",
            "event_chains": [chain],
            "quality_score": 0.8,
            "processing_time": 5.2,
            "errors": []
        }
        
        result = ExtractionResult(**result_data)
        assert result.document_id == "doc_001"
        assert len(result.event_chains) == 1
        assert result.quality_score == 0.8
    
    def test_prediction_request_valid(self):
        """测试创建有效预测请求"""
        request_data = {
            "hazard_description": "老旧建筑电气线路存在安全隐患",
            "prediction_type": ScenarioType.FIRE_EVOLUTION,
            "max_paths": 5,
            "max_depth": 3,
            "time_horizon": 1800
        }
        
        request = PredictionRequest(**request_data)
        assert request.hazard_description == "老旧建筑电气线路存在安全隐患"
        assert request.prediction_type == ScenarioType.FIRE_EVOLUTION
        assert request.max_paths == 5


if __name__ == "__main__":
    pytest.main([__file__])