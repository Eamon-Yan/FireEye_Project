"""
数据模型使用示例
"""

from datetime import datetime
from app.schemas import (
    EventChainCreate,
    RelationType,
    FireEventNode,
    EventType,
    ExtractionRequest,
    PredictionRequest,
    ScenarioType,
    DocumentCreate,
    FileType,
    UserCreate,
    UserRole,
)


def create_event_chain_example():
    """创建事件链示例"""
    print("=== 事件链创建示例 ===")
    
    # 创建事件链
    chain = EventChainCreate(
        source="电线老化",
        relation=RelationType.CAUSES,
        target="短路打火",
        confidence=0.85,
        timestamp=datetime.now(),
        context="老旧建筑电气线路，使用年限超过20年"
    )
    
    print(f"源事件: {chain.source}")
    print(f"关系类型: {chain.relation}")
    print(f"目标事件: {chain.target}")
    print(f"置信度: {chain.confidence}")
    print(f"上下文: {chain.context}")
    print()


def create_fire_event_node_example():
    """创建火灾事件节点示例"""
    print("=== 火灾事件节点创建示例 ===")
    
    # 创建火灾事件节点
    event_node = FireEventNode(
        id="event_001",
        event_type=EventType.CAUSE,
        description="电气线路老化导致绝缘层破损",
        standard_term="电气线路老化",
        category="电气火灾",
        severity_level=6,
        frequency=15
    )
    
    print(f"事件ID: {event_node.id}")
    print(f"事件类型: {event_node.event_type}")
    print(f"描述: {event_node.description}")
    print(f"标准术语: {event_node.standard_term}")
    print(f"严重程度: {event_node.severity_level}")
    print()


def create_extraction_request_example():
    """创建抽取请求示例"""
    print("=== 抽取请求创建示例 ===")
    
    # 创建抽取请求
    extraction_request = ExtractionRequest(
        document_id="doc_20240119_001",
        extraction_options={
            "extract_sections": ["事故经过", "原因分析"],
            "use_few_shot": True,
            "confidence_threshold": 0.7
        },
        priority=8
    )
    
    print(f"文档ID: {extraction_request.document_id}")
    print(f"抽取选项: {extraction_request.extraction_options}")
    print(f"优先级: {extraction_request.priority}")
    print()


def create_prediction_request_example():
    """创建预测请求示例"""
    print("=== 场景预测请求创建示例 ===")
    
    # 创建预测请求
    prediction_request = PredictionRequest(
        hazard_description="地下车库电动车充电桩线路老化，存在短路风险",
        prediction_type=ScenarioType.FIRE_EVOLUTION,
        max_paths=8,
        max_depth=4,
        time_horizon=2400,  # 40分钟
        include_script=True
    )
    
    print(f"隐患描述: {prediction_request.hazard_description}")
    print(f"预测类型: {prediction_request.prediction_type}")
    print(f"最大路径数: {prediction_request.max_paths}")
    print(f"时间范围: {prediction_request.time_horizon}秒")
    print()


def create_document_example():
    """创建文档示例"""
    print("=== 文档创建示例 ===")
    
    # 创建文档
    document = DocumentCreate(
        title="某商场火灾事故调查报告",
        file_type=FileType.PDF,
        metadata={
            "author": "消防调查组",
            "investigation_date": "2024-01-15",
            "location": "某市某商场",
            "incident_type": "电气火灾",
            "casualties": 0,
            "property_loss": 500000
        }
    )
    
    print(f"文档标题: {document.title}")
    print(f"文件类型: {document.file_type}")
    print(f"元数据: {document.metadata}")
    print()


def create_user_example():
    """创建用户示例"""
    print("=== 用户创建示例 ===")
    
    # 创建用户
    user = UserCreate(
        username="fire_analyst_001",
        email="analyst@fire-safety.com",
        password="SecurePass123!",
        full_name="张三",
        role=UserRole.ANALYST
    )
    
    print(f"用户名: {user.username}")
    print(f"邮箱: {user.email}")
    print(f"全名: {user.full_name}")
    print(f"角色: {user.role}")
    print()


def demonstrate_model_validation():
    """演示模型验证"""
    print("=== 模型验证示例 ===")
    
    try:
        # 尝试创建无效的事件链（置信度超出范围）
        invalid_chain = EventChainCreate(
            source="测试源",
            relation=RelationType.CAUSES,
            target="测试目标",
            confidence=1.5,  # 无效值
            context="测试"
        )
    except Exception as e:
        print(f"验证错误: {e}")
    
    try:
        # 尝试创建无效的火灾事件（严重程度超出范围）
        invalid_event = FireEventNode(
            id="test_001",
            event_type=EventType.CAUSE,
            description="测试描述",
            standard_term="测试术语",
            category="测试分类",
            severity_level=15,  # 无效值
            frequency=5
        )
    except Exception as e:
        print(f"验证错误: {e}")
    
    print()


def demonstrate_json_serialization():
    """演示JSON序列化"""
    print("=== JSON序列化示例 ===")
    
    # 创建事件链
    chain = EventChainCreate(
        source="电线老化",
        relation=RelationType.CAUSES,
        target="短路打火",
        confidence=0.85,
        context="老旧建筑电气线路"
    )
    
    # 序列化为JSON
    json_data = chain.model_dump()
    print("序列化为JSON:")
    print(json_data)
    
    # 从JSON反序列化
    restored_chain = EventChainCreate(**json_data)
    print(f"反序列化结果: {restored_chain.source} -> {restored_chain.target}")
    print()


if __name__ == "__main__":
    """运行所有示例"""
    print("火瞳系统数据模型使用示例")
    print("=" * 50)
    
    create_event_chain_example()
    create_fire_event_node_example()
    create_extraction_request_example()
    create_prediction_request_example()
    create_document_example()
    create_user_example()
    demonstrate_model_validation()
    demonstrate_json_serialization()
    
    print("所有示例运行完成！")