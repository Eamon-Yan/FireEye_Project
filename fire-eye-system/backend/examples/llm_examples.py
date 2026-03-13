"""
LLM服务使用示例和连接测试
"""

import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.llm_service import llm_service
from app.schemas.extraction import ExtractionConfig


async def test_llm_connection():
    """测试LLM API连接"""
    print("🔗 测试LLM API连接...")
    
    try:
        result = await llm_service.test_connection()
        
        if result["status"] == "success":
            print("✅ LLM连接测试成功!")
            print(f"   模型: {result['model']}")
            print(f"   响应: {result['response']}")
            print(f"   使用量: {result['usage']}")
        else:
            print("❌ LLM连接测试失败!")
            print(f"   错误: {result['error']}")
            
        return result["status"] == "success"
        
    except Exception as e:
        print(f"❌ 连接测试异常: {e}")
        return False


async def test_text_quality_analysis():
    """测试文本质量分析"""
    print("\n📊 测试文本质量分析...")
    
    test_texts = [
        "这是一个很短的文本",
        "今天天气很好，阳光明媚。",
        "2023年3月15日发生火灾，但没有详细信息。",
        """
        事故经过：2023年3月15日上午10:30，某工厂配电箱发生故障，电线绝缘层破损导致短路，
        产生电弧引燃了附近的包装材料，火势迅速蔓延。消防队及时赶到现场进行扑救。
        
        原因分析：经过调查，确定主要原因是电气线路老化，绝缘层破损导致短路起火。
        管理方面存在安全检查不到位的问题。
        """
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n   测试文本 {i}:")
        print(f"   内容: {text[:50]}...")
        
        quality = await llm_service.analyze_text_quality(text)
        
        print(f"   适合度: {'✅' if quality['suitable'] else '❌'}")
        print(f"   原因: {quality['reason']}")
        if quality['suggestions']:
            print(f"   建议: {'; '.join(quality['suggestions'])}")


async def test_event_chain_extraction():
    """测试事件链提取"""
    print("\n🔍 测试事件链提取...")
    
    # 测试文本
    test_text = """
    火灾事故调查报告
    
    事故经过：
    2023年5月20日下午14:30，某化工厂储罐区发生火灾爆炸事故。
    当时正值换班时间，现场有维修人员在进行设备检修。
    突然听到一声巨响，随即看到储罐冒出浓烟和火焰。
    现场人员立即启动应急预案，疏散人员并报警。
    消防队于14:45到达现场，经过3小时的扑救，火势完全扑灭。
    
    原因分析：
    经过专业机构的技术鉴定，确定事故原因为：
    主要原因：储罐内可燃气体泄漏遇到静电火花引燃
    次要原因：防静电接地系统失效，未能及时消除静电
    管理原因：安全检查不到位，未发现接地系统故障
    
    技术分析表明，储罐在检修过程中产生的静电未能及时导出，
    在可燃气体浓度达到爆炸极限时遇到静电火花发生爆燃。
    """
    
    print("   分析文本:")
    print(f"   {test_text[:100]}...")
    
    try:
        # 提取事件链
        event_chains = await llm_service.extract_event_chains(test_text)
        
        print(f"\n   ✅ 成功提取 {len(event_chains)} 个事件链:")
        
        for i, chain in enumerate(event_chains, 1):
            print(f"\n   事件链 {i}:")
            print(f"      源事件: {chain.source}")
            print(f"      关系: {chain.relation}")
            print(f"      目标事件: {chain.target}")
            print(f"      置信度: {chain.confidence:.2f}")
            print(f"      上下文: {chain.context}")
        
        return event_chains
        
    except Exception as e:
        print(f"   ❌ 事件链提取失败: {e}")
        return []


async def test_custom_config():
    """测试自定义配置"""
    print("\n⚙️ 测试自定义配置...")
    
    # 创建自定义配置
    custom_config = ExtractionConfig(
        llm_model="deepseek-chat",
        temperature=0.2,
        max_tokens=1500,
        extraction_prompt="""你是火灾分析专家。请从文本中提取因果关系，输出JSON格式。
        
输出格式：
{
  "event_chains": [
    {
      "source": "原因事件",
      "relation": "导致",
      "target": "结果事件", 
      "confidence": 0.8,
      "context": "背景信息"
    }
  ]
}""",
        quality_threshold=0.7
    )
    
    test_text = """
    住宅火灾调查：
    2023年6月10日凌晨，某小区发生火灾。
    起火原因是电热毯长时间通电导致过热，引燃了床上用品。
    火势迅速蔓延至整个房间，幸好及时发现并扑救。
    """
    
    try:
        event_chains = await llm_service.extract_event_chains(test_text, custom_config)
        
        print(f"   ✅ 使用自定义配置提取 {len(event_chains)} 个事件链")
        
        for chain in event_chains:
            print(f"      {chain.source} → {chain.relation} → {chain.target}")
            
    except Exception as e:
        print(f"   ❌ 自定义配置测试失败: {e}")


async def test_batch_extraction():
    """测试批量提取"""
    print("\n📦 测试批量事件链提取...")
    
    batch_texts = [
        """
        事故1：电气火灾
        电线老化导致短路，产生电弧引燃可燃物。
        """,
        """
        事故2：化学品火灾  
        化学品泄漏遇到高温引发爆燃，火势迅速扩散。
        """,
        """
        事故3：人为火灾
        违规操作导致设备过热，引燃周围材料。
        """
    ]
    
    try:
        results = await llm_service.batch_extract_event_chains(batch_texts)
        
        print(f"   ✅ 批量处理完成，共处理 {len(batch_texts)} 个文本")
        
        for i, chains in enumerate(results, 1):
            print(f"   文本 {i}: 提取 {len(chains)} 个事件链")
            
    except Exception as e:
        print(f"   ❌ 批量提取失败: {e}")


async def main():
    """主函数"""
    print("🔥 火瞳系统 - LLM服务测试")
    print("=" * 50)
    
    # 检查API密钥
    from app.core.config import settings
    if not settings.OPENAI_API_KEY:
        print("⚠️  警告: OPENAI_API_KEY 未设置")
        print("   请在 .env 文件中设置 OPENAI_API_KEY")
        print("   或设置环境变量 OPENAI_API_KEY")
        print("\n   示例 .env 配置:")
        print("   OPENAI_API_KEY=your_deepseek_api_key")
        print("   OPENAI_BASE_URL=https://api.deepseek.com")
        print("   OPENAI_MODEL=deepseek-chat")
        return
    
    print(f"📋 配置信息:")
    print(f"   API Base URL: {settings.OPENAI_BASE_URL}")
    print(f"   模型: {settings.OPENAI_MODEL}")
    print(f"   API Key: {'已设置' if settings.OPENAI_API_KEY else '未设置'}")
    
    # 运行测试
    connection_ok = await test_llm_connection()
    
    if connection_ok:
        await test_text_quality_analysis()
        await test_event_chain_extraction()
        await test_custom_config()
        await test_batch_extraction()
    else:
        print("\n❌ 由于连接失败，跳过其他测试")
        print("\n🔧 故障排除建议:")
        print("   1. 检查API密钥是否正确")
        print("   2. 检查网络连接")
        print("   3. 确认DeepSeek API服务状态")
        print("   4. 检查API配额是否充足")
    
    print("\n" + "=" * 50)
    print("✅ LLM服务测试完成!")


if __name__ == "__main__":
    asyncio.run(main())