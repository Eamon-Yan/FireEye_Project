"""
测试LLM服务文本质量分析功能
"""

import sys
import asyncio
sys.path.append('backend')

from app.services.llm_service import llm_service

async def test_quality():
    print('📊 测试文本质量分析功能...')
    
    test_texts = [
        '短文本',
        '这是一个关于天气的文本，没有火灾内容。',
        '火灾事故报告：2023年发生火灾，原因是电气线路老化导致短路起火。'
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f'\n测试文本 {i}: {text[:30]}...')
        quality = await llm_service.analyze_text_quality(text)
        suitable = '✅' if quality['suitable'] else '❌'
        print(f'   适合度: {suitable}')
        print(f'   原因: {quality["reason"]}')
        if quality['suggestions']:
            print(f'   建议: {quality["suggestions"][0]}')

if __name__ == "__main__":
    asyncio.run(test_quality())