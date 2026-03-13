"""
智能抽取服务使用示例
"""

import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock

from app.services.extraction_service import extraction_service, DocumentParser, SectionExtractor
from app.schemas.extraction import SectionType


async def demo_document_parsing():
    """演示文档解析功能"""
    print("=== 文档解析功能演示 ===")
    
    parser = DocumentParser()
    
    # 创建示例TXT文件
    sample_text = """
火灾调查报告

事故经过
2023年3月15日上午10:30，位于某市工业园区的ABC制造公司发生火灾。
当时车间内有工人正在进行生产作业，突然听到配电箱附近传来爆裂声，
随即看到火花四溅，引燃了附近堆放的包装材料。
工人立即按下紧急停机按钮并拨打119报警。
消防队于10:45到达现场，经过1小时的扑救，火势得到完全控制。

原因分析
经过现场勘查和技术分析，确定本次火灾的直接原因为：
1. 配电箱内主电缆绝缘层老化破损
2. 在高负荷运行时产生电弧放电
3. 电弧引燃了配电箱内的可燃物质
4. 火势蔓延至车间内的包装材料堆放区

根本原因分析：
- 企业对电气设备维护保养不到位
- 缺乏定期的电气安全检查
- 可燃物品堆放位置不当，距离电气设备过近

调查结果
本次火灾属于电气火灾，造成直接经济损失约50万元。
企业负有主要责任，存在安全管理不到位的问题。
建议加强电气设备维护，规范可燃物品存放。

预防措施
1. 立即更换老化的电气线路和设备
2. 建立定期电气安全检查制度
3. 重新规划车间布局，确保安全距离
4. 加强员工安全培训和应急演练
"""
    
    # 保存到临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(sample_text)
        temp_path = f.name
    
    try:
        # 解析文档
        from app.schemas.document import FileType
        parsed_text = parser.parse_document(temp_path, FileType.TXT)
        print(f"解析的文本长度: {len(parsed_text)} 字符")
        print(f"文本预览: {parsed_text[:100]}...")
        
    finally:
        os.unlink(temp_path)


def demo_section_extraction():
    """演示章节提取功能"""
    print("\n=== 章节提取功能演示 ===")
    
    extractor = SectionExtractor()
    
    sample_text = """
火灾调查报告

事故经过
2023年3月15日上午10:30，某工厂发生火灾事故。
火势从配电箱开始，迅速蔓延至车间内的可燃物品。
消防队及时赶到现场，经过1小时扑救，火势得到控制。
事故造成部分设备损坏，但无人员伤亡。

原因分析
经过现场勘查和技术分析，确定火灾原因如下：
1. 配电箱内电缆绝缘层老化
2. 高负荷运行时产生电弧
3. 电弧引燃周围可燃物
4. 安全管理存在漏洞

调查结果
本次火灾属于电气火灾，企业负主要责任。
建议加强电气设备维护和安全管理。

预防措施
1. 更换老化电气设备
2. 建立定期检查制度
3. 加强员工培训
4. 完善应急预案
"""
    
    # 提取章节
    sections = extractor.extract_sections(sample_text)
    
    print(f"提取到 {len(sections)} 个章节:")
    for section_name, content in sections.items():
        print(f"\n【{section_name}】")
        print(f"内容长度: {len(content)} 字符")
        print(f"内容预览: {content[:100]}...")


async def demo_full_extraction_service():
    """演示完整的抽取服务功能"""
    print("\n=== 完整抽取服务演示 ===")
    
    # 创建模拟的上传文件
    mock_file = Mock()
    mock_file.filename = "fire_report.txt"
    
    sample_content = """
火灾事故调查报告

事故经过
2023年5月20日下午14:30，某化工厂储罐区发生火灾爆炸事故。
当时正值换班时间，现场有维修人员在进行设备检修。
突然听到一声巨响，随即看到储罐冒出浓烟和火焰。
现场人员立即启动应急预案，疏散人员并报警。
消防队于14:45到达现场，经过3小时的扑救，火势完全扑灭。

原因分析
经过专业机构的技术鉴定，确定事故原因为：
主要原因：储罐内可燃气体泄漏遇到静电火花引燃
次要原因：防静电接地系统失效，未能及时消除静电
管理原因：安全检查不到位，未发现接地系统故障

技术分析表明，储罐在检修过程中产生的静电未能及时导出，
在可燃气体浓度达到爆炸极限时遇到静电火花发生爆燃。
"""
    
    # 模拟文件读取
    async def mock_read():
        return sample_content.encode('utf-8')
    
    mock_file.read = mock_read
    
    try:
        # 处理文档
        document_id, document_sections = await extraction_service.process_document(mock_file)
        
        print(f"文档ID: {document_id}")
        print(f"提取的章节数量: {len(document_sections.sections)}")
        
        for section_name, content in document_sections.sections.items():
            print(f"\n【{section_name}】")
            print(f"字符数: {len(content)}")
            print(f"内容: {content[:200]}...")
        
        # 验证章节
        errors = extraction_service.validate_sections(document_sections.sections)
        if errors:
            print(f"\n验证错误: {errors}")
        else:
            print("\n✓ 章节验证通过")
            
    except Exception as e:
        print(f"处理失败: {e}")


def demo_section_patterns():
    """演示章节识别模式"""
    print("\n=== 章节识别模式演示 ===")
    
    extractor = SectionExtractor()
    
    # 测试不同的章节标题格式
    test_cases = [
        "事故经过：详细描述...",
        "一、火灾过程\n内容...",
        "2. 原因分析\n分析内容...",
        "（三）调查结果\n结果内容...",
        "四、预防措施建议\n建议内容..."
    ]
    
    print("支持的章节识别模式:")
    for section_type, patterns in extractor.section_patterns.items():
        print(f"\n{section_type.value}:")
        for pattern in patterns:
            print(f"  - {pattern}")
    
    print("\n测试章节标题识别:")
    for test_case in test_cases:
        sections = extractor.extract_sections(test_case)
        if sections:
            section_names = list(sections.keys())
            print(f"'{test_case[:20]}...' -> {section_names}")
        else:
            print(f"'{test_case[:20]}...' -> 未识别")


async def main():
    """主函数"""
    print("智能抽取服务功能演示")
    print("=" * 50)
    
    # 演示各个功能模块
    await demo_document_parsing()
    demo_section_extraction()
    await demo_full_extraction_service()
    demo_section_patterns()
    
    print("\n" + "=" * 50)
    print("演示完成！")


if __name__ == "__main__":
    asyncio.run(main())