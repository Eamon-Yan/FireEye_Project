"""
LLM集成服务
支持DeepSeek API进行事件链抽取
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from openai import AsyncOpenAI
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.extraction import LLMResponse, ExtractionConfig
from app.schemas.event_chain import EventChain, EventChainCreate, RelationType

logger = logging.getLogger(__name__)


class LLMService:
    """LLM服务类，用于事件链抽取"""
    
    def __init__(self):
        """初始化LLM服务"""
        self.client = None
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL
        self.model = settings.OPENAI_MODEL
        
        # 火灾事件专家系统提示词
        self.system_prompt = self._create_fire_expert_prompt()
        
        # Few-Shot示例
        self.few_shot_examples = self._create_few_shot_examples()
        
        logger.info(f"LLM服务初始化 - 模型: {self.model}, 基础URL: {self.base_url}")
    
    async def initialize(self) -> None:
        """初始化异步客户端"""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY未设置，请在环境变量中配置")
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        logger.info("LLM客户端初始化成功")
    
    def _create_fire_expert_prompt(self) -> str:
        """创建火灾事件专家系统提示词"""
        return """你是一位专业的火灾事故调查专家，具有丰富的火灾原因分析和事故调查经验。

你的任务是分析火灾事故报告文本，从中提取事件链（因果关系链）。

## 分析要求：
1. 仔细阅读提供的火灾事故文本
2. 识别其中的因果关系，包括：
   - 直接原因（导致火灾发生的直接因素）
   - 间接原因（促成火灾发生的背景因素）
   - 过程事件（火灾发展过程中的关键事件）
   - 结果事件（火灾造成的后果）

## 关系类型定义：
- "导致": 直接的因果关系，A导致B发生
- "促进": A促进了B的发生或发展
- "触发": A触发了B事件
- "加速": A加速了B的进程
- "阻止": A阻止了B的发生（用于描述防护措施等）

## 输出格式：
必须严格按照以下JSON格式输出，不要包含任何其他文字：

```json
{
  "event_chains": [
    {
      "source": "源事件描述",
      "relation": "关系类型",
      "target": "目标事件描述",
      "confidence": 0.85,
      "context": "上下文信息"
    }
  ]
}
```

## 注意事项：
- source和target必须是具体的事件描述，不超过50字
- relation必须是上述定义的关系类型之一
- confidence是0-1之间的数值，表示该因果关系的可信度
- context提供该因果关系的上下文背景
- 只输出JSON格式，不要包含解释性文字
- 确保JSON格式正确，可以被程序解析"""

    def _create_few_shot_examples(self) -> List[Dict[str, Any]]:
        """创建Few-Shot学习示例"""
        return [
            {
                "input": """事故经过：2023年3月15日，某工厂配电箱发生故障，电线绝缘层破损导致短路，产生电弧引燃了附近的包装材料，火势迅速蔓延。
原因分析：电气线路老化是主要原因，安全检查不到位是管理原因。""",
                "output": {
                    "event_chains": [
                        {
                            "source": "电线绝缘层破损",
                            "relation": "导致",
                            "target": "电路短路",
                            "confidence": 0.95,
                            "context": "配电箱内电线老化导致绝缘失效"
                        },
                        {
                            "source": "电路短路",
                            "relation": "导致",
                            "target": "产生电弧",
                            "confidence": 0.90,
                            "context": "短路时产生高温电弧"
                        },
                        {
                            "source": "产生电弧",
                            "relation": "导致",
                            "target": "引燃包装材料",
                            "confidence": 0.85,
                            "context": "电弧高温引燃附近可燃物"
                        },
                        {
                            "source": "引燃包装材料",
                            "relation": "导致",
                            "target": "火势蔓延",
                            "confidence": 0.80,
                            "context": "可燃材料助长火势扩散"
                        },
                        {
                            "source": "电气线路老化",
                            "relation": "导致",
                            "target": "电线绝缘层破损",
                            "confidence": 0.90,
                            "context": "长期使用导致线路老化"
                        },
                        {
                            "source": "安全检查不到位",
                            "relation": "促进",
                            "target": "电气线路老化",
                            "confidence": 0.75,
                            "context": "缺乏定期检查导致隐患未及时发现"
                        }
                    ]
                }
            }
        ]
    
    async def extract_event_chains(
        self,
        text: str,
        config: Optional[ExtractionConfig] = None
    ) -> List[EventChainCreate]:
        """
        从文本中提取事件链
        
        Args:
            text: 待分析的文本内容
            config: 抽取配置参数
            
        Returns:
            提取的事件链列表
        """
        if not self.client:
            await self.initialize()
        
        # 使用默认配置或提供的配置
        if config is None:
            config = ExtractionConfig(
                llm_model=self.model,
                temperature=0.1,
                max_tokens=2000,
                extraction_prompt=self.system_prompt
            )
        
        try:
            # 构建消息
            messages = self._build_messages(text, config)
            
            # 调用LLM API
            start_time = datetime.now()
            response = await self.client.chat.completions.create(
                model=config.llm_model,
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                response_format={"type": "json_object"}  # 强制JSON输出
            )
            end_time = datetime.now()
            
            # 解析响应
            llm_response = LLMResponse(
                content=response.choices[0].message.content,
                usage=response.usage.model_dump() if hasattr(response.usage, 'model_dump') else dict(response.usage),
                model=response.model,
                finish_reason=response.choices[0].finish_reason,
                response_time=(end_time - start_time).total_seconds()
            )
            
            # 解析事件链
            event_chains = self._parse_event_chains(llm_response.content)
            
            logger.info(f"成功提取 {len(event_chains)} 个事件链，耗时 {llm_response.response_time:.2f}秒")
            
            return event_chains
            
        except Exception as e:
            logger.error(f"事件链提取失败: {e}")
            raise
    
    def _build_messages(self, text: str, config: ExtractionConfig) -> List[Dict[str, str]]:
        """构建LLM消息"""
        messages = [
            {"role": "system", "content": config.extraction_prompt}
        ]
        
        # 添加Few-Shot示例
        for example in config.few_shot_examples or self.few_shot_examples:
            messages.append({
                "role": "user", 
                "content": f"请分析以下火灾事故文本：\n\n{example['input']}"
            })
            messages.append({
                "role": "assistant", 
                "content": json.dumps(example['output'], ensure_ascii=False, indent=2)
            })
        
        # 添加实际要分析的文本
        messages.append({
            "role": "user",
            "content": f"请分析以下火灾事故文本：\n\n{text}"
        })
        
        return messages
    
    def _parse_event_chains(self, llm_output: str) -> List[EventChainCreate]:
        """解析LLM输出的事件链"""
        try:
            # 解析JSON
            data = json.loads(llm_output)
            
            if "event_chains" not in data:
                raise ValueError("LLM输出格式错误：缺少event_chains字段")
            
            event_chains = []
            for chain_data in data["event_chains"]:
                try:
                    # 验证关系类型
                    relation = chain_data.get("relation", "")
                    if relation not in [r.value for r in RelationType]:
                        logger.warning(f"未知关系类型: {relation}，使用默认值'导致'")
                        relation = RelationType.CAUSES.value
                    
                    # 创建事件链对象
                    event_chain = EventChainCreate(
                        source=chain_data.get("source", "").strip(),
                        relation=RelationType(relation),
                        target=chain_data.get("target", "").strip(),
                        confidence=float(chain_data.get("confidence", 0.5)),
                        context=chain_data.get("context", "").strip()
                    )
                    
                    event_chains.append(event_chain)
                    
                except (ValidationError, ValueError, KeyError) as e:
                    logger.warning(f"跳过无效事件链: {chain_data}, 错误: {e}")
                    continue
            
            return event_chains
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"LLM输出内容: {llm_output}")
            raise ValueError(f"LLM输出不是有效的JSON格式: {e}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """测试LLM API连接"""
        if not self.client:
            await self.initialize()
        
        try:
            # 发送简单的测试请求
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个测试助手。"},
                    {"role": "user", "content": "请回复'连接测试成功'"}
                ],
                max_tokens=50,
                temperature=0
            )
            
            return {
                "status": "success",
                "model": response.model,
                "response": response.choices[0].message.content,
                "usage": response.usage.model_dump() if hasattr(response.usage, 'model_dump') else dict(response.usage)
            }
            
        except Exception as e:
            logger.error(f"LLM连接测试失败: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def analyze_text_quality(self, text: str) -> Dict[str, Any]:
        """分析文本质量，评估是否适合事件链提取"""
        if not text or len(text.strip()) < 50:
            return {
                "suitable": False,
                "reason": "文本内容过短",
                "suggestions": ["请提供更详细的事故描述"]
            }
        
        # 检查是否包含关键词
        fire_keywords = ["火灾", "起火", "燃烧", "爆炸", "烟雾", "火势", "扑救", "消防"]
        cause_keywords = ["原因", "导致", "引起", "造成", "由于", "因为"]
        
        has_fire_content = any(keyword in text for keyword in fire_keywords)
        has_cause_content = any(keyword in text for keyword in cause_keywords)
        
        if not has_fire_content:
            return {
                "suitable": False,
                "reason": "文本不包含火灾相关内容",
                "suggestions": ["请确认文本是火灾事故报告"]
            }
        
        if not has_cause_content:
            return {
                "suitable": True,
                "reason": "文本包含火灾内容但缺少原因分析",
                "suggestions": ["建议补充原因分析内容以获得更好的提取效果"]
            }
        
        return {
            "suitable": True,
            "reason": "文本适合进行事件链提取",
            "suggestions": []
        }
    
    async def batch_extract_event_chains(
        self,
        texts: List[str],
        config: Optional[ExtractionConfig] = None
    ) -> List[List[EventChainCreate]]:
        """批量提取事件链"""
        results = []
        
        for i, text in enumerate(texts):
            try:
                logger.info(f"处理第 {i+1}/{len(texts)} 个文本")
                event_chains = await self.extract_event_chains(text, config)
                results.append(event_chains)
                
                # 添加延迟以避免API限制
                if i < len(texts) - 1:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"第 {i+1} 个文本处理失败: {e}")
                results.append([])
        
        return results


# 全局LLM服务实例
llm_service = LLMService()