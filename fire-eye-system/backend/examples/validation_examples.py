"""
校验对齐服务使用示例和测试
"""

import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.validation_service import validation_service
from app.services.llm_service import llm_service
from app.schemas.event_chain import EventChainCreate, RelationType


async def test_terminology_normalization():
    """测试术语归一化功能"""
    print("🔧 测试术语归一化...")
    
    test_texts = [
        "电瓶车充电时发生短路",
        "电单车电池过热导致起火",
        "电动车充电器故障引起燃烧",
        "配电箱内电线老化导致漏电",
        "插座接触不良产生电弧",
        "储藏室内堆放大量塑料制品"
    ]
    
    for i, text in enumerate(test_texts, 1):
        normalized = validation_service.normalize_terminology(text)
        print(f"   测试 {i}:")
        print(f"      原文: {text}")
        print(f"      归一化: {normalized}")
        
        # 获取建议
        suggestions = validation_service.get_terminology_suggestions(text)
        if suggestions:
            print(f"      建议: {'; '.join(suggestions)}")
        print()


async def test_event_chain_validation():
    """测试事件链验证功能"""
    print("✅ 测试事件链验证...")
    
    # 创建测试事件链
    test_chains = [
        # 有效事件链
        EventChainCreate(
            source="电瓶车充电器过热",
            relation=RelationType.CAUSES,
            target="引燃周围可燃物",
            confidence=0.85,
            context="充电器长时间工作导致过热"
        ),
        # 置信度过低的事件链
        EventChainCreate(
            source="天气炎热",
            relation=RelationType.CAUSES,
            target="火灾发生",
            confidence=0.3,
            context="天气因素影响"
        ),
        # 源事件为空的事件链
        EventChainCreate(
            source="",
            relation=RelationType.CAUSES,
            target="设备损坏",
            confidence=0.8,
            context="测试空源事件"
        ),
        # 源事件和目标事件相同的事件链
        EventChainCreate(
            source="电路短路",
            relation=RelationType.CAUSES,
            target="电路短路",
            confidence=0.9,
            context="循环引用测试"
        ),
        # 包含时间信息的事件链
        EventChainCreate(
            source="2023年3月15日上午10:30发生短路",
            relation=RelationType.CAUSES,
            target="2023年3月15日上午10:35起火",
            confidence=0.9,
            context="时间序列测试"
        )
    ]
    
    for i, chain in enumerate(test_chains, 1):
        print(f"   事件链 {i}:")
        print(f"      源事件: {chain.source}")
        print(f"      关系: {chain.relation}")
        print(f"      目标事件: {chain.target}")
        print(f"      置信度: {chain.confidence}")
        
        # 验证事件链
        result = validation_service.validate_event_chain(chain)
        
        print(f"      验证结果: {'✅ 有效' if result.is_valid else '❌ 无效'}")
        if result.errors:
            print(f"      错误: {'; '.join(result.errors)}")
        if result.warnings:
            print(f"      警告: {'; '.join(result.warnings)}")
        print()


async def test_batch_validation():
    """测试批量验证功能"""
    print("📦 测试批量验证...")
    
    # 创建混合质量的事件链列表
    test_chains = [
        EventChainCreate(
            source="电线老化",
            relation=RelationType.CAUSES,
            target="绝缘层破损",
            confidence=0.9,
            context="长期使用导致老化"
        ),
        EventChainCreate(
            source="绝缘层破损",
            relation=RelationType.CAUSES,
            target="电路短路",
            confidence=0.85,
            context="绝缘失效导致短路"
        ),
        EventChainCreate(
            source="电路短路",
            relation=RelationType.CAUSES,
            target="产生电弧",
            confidence=0.8,
            context="短路产生高温电弧"
        ),
        EventChainCreate(
            source="产生电弧",
            relation=RelationType.CAUSES,
            target="引燃可燃物",
            confidence=0.75,
            context="电弧高温引燃附近物品"
        ),
        # 低质量事件链
        EventChainCreate(
            source="天气",
            relation=RelationType.CAUSES,
            target="火灾",
            confidence=0.2,
            context="质量较低的事件链"
        ),
        EventChainCreate(
            source="",
            relation=RelationType.CAUSES,
            target="损坏",
            confidence=0.5,
            context="空源事件测试"
        )
    ]
    
    # 批量验证
    valid_chains, validation_results = validation_service.filter_valid_chains(
        test_chains, 
        apply_normalization=True
    )
    
    print(f"   输入事件链: {len(test_chains)} 个")
    print(f"   有效事件链: {len(valid_chains)} 个")
    print(f"   过滤事件链: {len(test_chains) - len(valid_chains)} 个")
    
    # 获取统计信息
    stats = validation_service.get_validation_statistics(validation_results)
    print(f"   验证通过率: {stats['validation_rate']:.2%}")
    print(f"   平均置信度: {stats['avg_confidence']:.2f}")
    
    if stats['common_errors']:
        print("   常见错误:")
        for error, count in stats['common_errors']:
            print(f"      - {error}: {count} 次")
    
    print("\n   有效事件链详情:")
    for i, chain in enumerate(valid_chains, 1):
        print(f"      {i}. {chain.source} → {chain.relation.value} → {chain.target}")


async def test_llm_integration():
    """测试与LLM服务的集成"""
    print("🤖 测试LLM集成验证...")
    
    # 测试文本
    test_text = """
    火灾事故报告：
    2023年6月10日下午14:30，某住宅小区发生火灾。
    起火原因是电瓶车在楼道内充电时，充电器发生故障导致过热，
    引燃了电单车的塑料外壳，火势迅速蔓延至楼道内的杂物。
    消防队及时赶到现场进行扑救，火势得到控制。
    
    经调查，主要原因是电动车充电设备老化，加上楼道内堆放可燃物品，
    为火势蔓延提供了条件。管理方面存在安全检查不到位的问题。
    """
    
    try:
        # 使用LLM提取事件链
        print("   使用LLM提取事件链...")
        raw_chains = await llm_service.extract_event_chains(test_text)
        print(f"   LLM提取结果: {len(raw_chains)} 个事件链")
        
        # 应用验证和归一化
        print("   应用验证和归一化...")
        valid_chains, validation_results = validation_service.filter_valid_chains(
            raw_chains,
            apply_normalization=True
        )
        
        print(f"   验证结果: {len(valid_chains)}/{len(raw_chains)} 个事件链通过验证")
        
        # 显示对比结果
        print("\n   原始 vs 归一化对比:")
        for i, (raw_chain, valid_chain) in enumerate(zip(raw_chains[:3], valid_chains[:3]), 1):
            print(f"      事件链 {i}:")
            print(f"         原始源事件: {raw_chain.source}")
            print(f"         归一化源事件: {valid_chain.source}")
            print(f"         原始目标事件: {raw_chain.target}")
            print(f"         归一化目标事件: {valid_chain.target}")
            print()
        
        # 获取统计信息
        stats = validation_service.get_validation_statistics(validation_results)
        print(f"   验证统计:")
        print(f"      通过率: {stats['validation_rate']:.2%}")
        print(f"      平均置信度: {stats['avg_confidence']:.2f}")
        
    except Exception as e:
        print(f"   ❌ LLM集成测试失败: {e}")


async def test_confidence_threshold():
    """测试置信度阈值调整"""
    print("🎯 测试置信度阈值调整...")
    
    # 创建不同置信度的事件链
    test_chains = [
        EventChainCreate(
            source="电线老化",
            relation=RelationType.CAUSES,
            target="短路起火",
            confidence=0.9,
            context="高置信度事件链"
        ),
        EventChainCreate(
            source="管理不善",
            relation=RelationType.PROMOTES,
            target="安全隐患",
            confidence=0.7,
            context="中等置信度事件链"
        ),
        EventChainCreate(
            source="天气因素",
            relation=RelationType.PROMOTES,
            target="火灾风险",
            confidence=0.5,
            context="低置信度事件链"
        )
    ]
    
    # 测试不同阈值
    thresholds = [0.4, 0.6, 0.8]
    
    for threshold in thresholds:
        print(f"\n   阈值设置为 {threshold}:")
        validation_service.update_confidence_threshold(threshold)
        
        valid_chains, _ = validation_service.filter_valid_chains(test_chains)
        print(f"      通过验证的事件链: {len(valid_chains)}/{len(test_chains)} 个")
        
        for chain in valid_chains:
            print(f"         - {chain.source} (置信度: {chain.confidence})")
    
    # 恢复默认阈值
    validation_service.update_confidence_threshold(0.6)


async def test_time_validation():
    """测试时间逻辑验证"""
    print("⏰ 测试时间逻辑验证...")
    
    time_test_chains = [
        # 正确的时间顺序
        EventChainCreate(
            source="上午10:30发生短路",
            relation=RelationType.CAUSES,
            target="上午10:35起火",
            confidence=0.8,
            context="正确时间顺序"
        ),
        # 错误的时间顺序
        EventChainCreate(
            source="下午15:30发现火情",
            relation=RelationType.CAUSES,
            target="下午14:00设备故障",
            confidence=0.8,
            context="错误时间顺序"
        ),
        # 包含日期的时间
        EventChainCreate(
            source="2023年3月15日上午发生故障",
            relation=RelationType.CAUSES,
            target="2023年3月15日下午起火",
            confidence=0.8,
            context="跨时段事件"
        )
    ]
    
    for i, chain in enumerate(time_test_chains, 1):
        print(f"   时间测试 {i}:")
        print(f"      源事件: {chain.source}")
        print(f"      目标事件: {chain.target}")
        
        result = validation_service.validate_event_chain(chain)
        print(f"      验证结果: {'✅ 有效' if result.is_valid else '❌ 无效'}")
        
        if result.warnings:
            print(f"      时间警告: {'; '.join(result.warnings)}")
        print()


async def main():
    """主函数"""
    print("🔥 火瞳系统 - 校验对齐服务测试")
    print("=" * 60)
    
    # 检查术语映射是否加载
    print(f"📋 术语映射规则数量: {len(validation_service.terminology_mapping)}")
    print(f"📋 当前置信度阈值: {validation_service.confidence_threshold}")
    print()
    
    # 运行各项测试
    await test_terminology_normalization()
    await test_event_chain_validation()
    await test_batch_validation()
    await test_confidence_threshold()
    await test_time_validation()
    await test_llm_integration()
    
    print("=" * 60)
    print("✅ 校验对齐服务测试完成!")


if __name__ == "__main__":
    asyncio.run(main())