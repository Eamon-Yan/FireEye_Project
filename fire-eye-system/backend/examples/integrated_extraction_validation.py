"""
集成抽取和校验服务示例
演示完整的文档处理 -> 事件链提取 -> 验证归一化流程
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.extraction_service import extraction_service
from app.services.validation_service import validation_service
from app.services.llm_service import llm_service
from app.schemas.extraction import DocumentSections


async def test_integrated_workflow():
    """测试集成工作流程"""
    print("🔥 火瞳系统 - 集成抽取验证工作流程测试")
    print("=" * 60)
    
    # 模拟文档内容
    mock_document_sections = DocumentSections(sections={
        "事故经过": """
        2023年8月15日下午15:30，某住宅小区地下车库发生火灾。
        当时有居民发现电瓶车充电区域冒出浓烟，随即听到爆炸声。
        起火的是一辆正在充电的电单车，火势迅速蔓延至附近停放的其他电动车。
        现场堆放的纸箱、塑料制品等可燃物助长了火势。
        小区保安立即报警并组织人员疏散，消防队于16:00到达现场。
        经过1小时的扑救，火势完全扑灭，但已造成5辆电瓶车烧毁。
        """,
        "原因分析": """
        经过专业机构调查，确定事故原因如下：
        主要原因：电动车充电器长期使用导致老化，内部电路短路产生高温，
        引燃了充电器外壳的塑料材料，进而点燃电池组。
        次要原因：地下车库通风不良，可燃气体积聚；
        车库内违规堆放大量纸张、橡胶等易燃物品。
        管理原因：物业管理不善，缺乏定期的安全检查，
        未及时发现和更换老化的充电设备。
        """
    })
    
    print("📋 模拟文档章节:")
    for section_name, content in mock_document_sections.sections.items():
        print(f"   {section_name}: {len(content)} 字符")
    print()
    
    # 步骤1: 提取事件链
    print("🔍 步骤1: 使用LLM提取事件链...")
    event_chains, processing_stats = await extraction_service.extract_and_validate_event_chains(
        mock_document_sections,
        apply_validation=False  # 先不应用验证，看原始结果
    )
    
    print(f"   提取结果: {len(event_chains)} 个原始事件链")
    print("   原始事件链:")
    for i, chain in enumerate(event_chains[:5], 1):  # 只显示前5个
        print(f"      {i}. {chain.source} → {chain.relation.value} → {chain.target}")
        print(f"         置信度: {chain.confidence:.2f}")
    if len(event_chains) > 5:
        print(f"      ... 还有 {len(event_chains) - 5} 个事件链")
    print()
    
    # 步骤2: 应用术语归一化
    print("🔧 步骤2: 应用术语归一化...")
    normalized_chains = []
    for chain in event_chains:
        normalized_chain = validation_service._normalize_event_chain(chain)
        normalized_chains.append(normalized_chain)
    
    print("   术语归一化对比 (前3个):")
    for i, (original, normalized) in enumerate(zip(event_chains[:3], normalized_chains[:3]), 1):
        print(f"      事件链 {i}:")
        if original.source != normalized.source:
            print(f"         源事件: {original.source} → {normalized.source}")
        if original.target != normalized.target:
            print(f"         目标事件: {original.target} → {normalized.target}")
        if original.source == normalized.source and original.target == normalized.target:
            print(f"         无需归一化: {original.source} → {original.target}")
    print()
    
    # 步骤3: 应用逻辑校验
    print("✅ 步骤3: 应用逻辑校验...")
    valid_chains, validation_results = validation_service.filter_valid_chains(
        event_chains,
        apply_normalization=True
    )
    
    print(f"   校验结果: {len(valid_chains)}/{len(event_chains)} 个事件链通过验证")
    
    # 获取验证统计
    stats = validation_service.get_validation_statistics(validation_results)
    print(f"   验证通过率: {stats['validation_rate']:.2%}")
    print(f"   平均置信度: {stats['avg_confidence']:.2f}")
    
    if stats['common_errors']:
        print("   常见错误:")
        for error, count in stats['common_errors'][:3]:
            print(f"      - {error}: {count} 次")
    print()
    
    # 步骤4: 显示最终结果
    print("🎯 步骤4: 最终验证通过的事件链:")
    for i, chain in enumerate(valid_chains, 1):
        print(f"   {i}. {chain.source}")
        print(f"      → {chain.relation.value} →")
        print(f"      {chain.target}")
        print(f"      置信度: {chain.confidence:.2f} | 上下文: {chain.context[:50]}...")
        print()
    
    return valid_chains, processing_stats


async def test_quality_analysis():
    """测试文档质量分析"""
    print("📊 文档质量分析测试")
    print("-" * 40)
    
    # 高质量文档
    high_quality_doc = DocumentSections(sections={
        "事故经过": """
        2023年9月20日上午10:15，某工厂配电室发生火灾。
        当时电工正在进行设备维护，突然听到配电箱内传出异响，
        随即看到电弧闪光和烟雾冒出。电工立即切断主电源，
        但配电箱内的绝缘材料已经起火，火势迅速蔓延。
        """,
        "原因分析": """
        经调查确定，主要原因是配电箱内电缆绝缘层老化破损，
        导致相间短路产生电弧，高温引燃了绝缘材料。
        管理方面存在定期检查不到位的问题。
        """
    })
    
    # 低质量文档
    low_quality_doc = DocumentSections(sections={
        "事故经过": "发生了火灾，很严重。",
        "原因分析": "不知道什么原因。"
    })
    
    # 分析高质量文档
    print("   高质量文档分析:")
    high_quality_analysis = await extraction_service.analyze_document_quality(high_quality_doc)
    print(f"      文本适合度: {'✅' if high_quality_analysis['text_quality']['suitable'] else '❌'}")
    print(f"      适合原因: {high_quality_analysis['text_quality']['reason']}")
    print(f"      章节数量: {high_quality_analysis['section_count']}")
    print(f"      总长度: {high_quality_analysis['total_length']} 字符")
    if high_quality_analysis['terminology_suggestions']:
        print(f"      术语建议: {len(high_quality_analysis['terminology_suggestions'])} 条")
    
    # 分析低质量文档
    print("\n   低质量文档分析:")
    low_quality_analysis = await extraction_service.analyze_document_quality(low_quality_doc)
    print(f"      文本适合度: {'✅' if low_quality_analysis['text_quality']['suitable'] else '❌'}")
    print(f"      适合原因: {low_quality_analysis['text_quality']['reason']}")
    print(f"      章节数量: {low_quality_analysis['section_count']}")
    print(f"      总长度: {low_quality_analysis['total_length']} 字符")
    if low_quality_analysis['text_quality']['suggestions']:
        print(f"      改进建议: {'; '.join(low_quality_analysis['text_quality']['suggestions'])}")
    print()


async def test_confidence_filtering():
    """测试置信度过滤效果"""
    print("🎯 置信度过滤效果测试")
    print("-" * 40)
    
    # 创建不同置信度的测试文档
    test_doc = DocumentSections(sections={
        "事故经过": """
        电线可能老化了，然后可能短路了，可能引起了火灾。
        也有可能是其他原因，不太确定。天气很热，可能也有影响。
        """,
        "原因分析": """
        主要原因应该是电气故障，具体是电线绝缘层破损导致短路。
        次要原因可能包括环境温度过高，设备维护不当等。
        """
    })
    
    # 测试不同置信度阈值的效果
    thresholds = [0.4, 0.6, 0.8]
    
    for threshold in thresholds:
        print(f"   置信度阈值: {threshold}")
        
        # 更新阈值
        validation_service.update_confidence_threshold(threshold)
        
        # 提取和验证
        valid_chains, _ = await extraction_service.extract_and_validate_event_chains(
            test_doc,
            apply_validation=True
        )
        
        print(f"      通过验证的事件链: {len(valid_chains)} 个")
        
        if valid_chains:
            avg_confidence = sum(chain.confidence for chain in valid_chains) / len(valid_chains)
            print(f"      平均置信度: {avg_confidence:.2f}")
            print(f"      置信度范围: {min(chain.confidence for chain in valid_chains):.2f} - {max(chain.confidence for chain in valid_chains):.2f}")
        print()
    
    # 恢复默认阈值
    validation_service.update_confidence_threshold(0.6)


async def main():
    """主函数"""
    print("🚀 启动集成测试...")
    print()
    
    # 检查服务状态
    print("📋 服务状态检查:")
    print(f"   术语映射规则: {len(validation_service.terminology_mapping)} 条")
    print(f"   置信度阈值: {validation_service.confidence_threshold}")
    
    # 测试LLM连接
    llm_status = await llm_service.test_connection()
    print(f"   LLM服务: {'✅ 正常' if llm_status['status'] == 'success' else '❌ 异常'}")
    print()
    
    # 运行集成测试
    try:
        valid_chains, stats = await test_integrated_workflow()
        
        print("📈 处理统计:")
        print(f"   原始事件链: {stats['raw_chains']} 个")
        print(f"   有效事件链: {stats['valid_chains']} 个")
        print(f"   过滤事件链: {stats['filtered_chains']} 个")
        print(f"   验证通过率: {stats['validation_rate']:.2%}")
        print(f"   平均置信度: {stats['avg_confidence']:.2f}")
        print()
        
        # 运行其他测试
        await test_quality_analysis()
        await test_confidence_filtering()
        
        print("=" * 60)
        print("✅ 集成测试完成! 所有功能正常运行。")
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())