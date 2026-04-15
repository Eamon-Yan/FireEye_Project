"""
LLM集成服务
支持DeepSeek API进行分层事件链抽取
"""

import json
import logging
from copy import deepcopy
from typing import Dict, List, Optional, Any
from datetime import datetime

from openai import AsyncOpenAI
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.extraction import (
    LLMResponse,
    ExtractionConfig,
    LayeredExtractionResult,
    ExtractedNode,
    ExtractedEdge,
    ExtractedNodeType,
    ExtractedRelationType,
)
from app.schemas.event_chain import EventChainCreate

logger = logging.getLogger(__name__)


class LLMService:
    """LLM服务类，用于分层事件链抽取"""
    
    def __init__(self):
        """初始化LLM服务"""
        self.client = None
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL
        self.model = settings.OPENAI_MODEL
        
        self.system_prompt = self._create_fire_expert_prompt()
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

你的任务是分析火灾事故报告文本，并以“隐患(Hazard) -> 火灾事件(FireEvent) -> 后果(Consequence)”的分层结构抽取知识图谱。

## 分析要求：
1. 仔细阅读提供的火灾事故文本。
2. 识别其中的三类节点：
   - Hazard：起火前的隐患、缺陷、管理漏洞、不安全状态。
   - FireEvent：起火、蔓延、爆燃、扑救等火灾过程中的关键事件。
   - Consequence：人员伤亡、财产损失、停产停业、建筑受损等后果。
3. 识别节点之间的关系，仅允许以下关系：
   - LEADS_TO：隐患逐步导向某个火灾事件。
   - CAUSES：前一节点直接导致后一节点。
   - RESULTS_IN：火灾事件最终造成某种后果。

## 严格约束：
1. 节点尽量使用报告中的原始表述，并提炼一个简短标准术语 standard_term。
2. 不要把“短路、漏电、绝缘破损、违规堆放、管理不到位”等隐患误判为 FireEvent，除非文本明确描述其作为实际发生的火灾过程事件。
3. 不要把“烧毁、死亡、受伤、损失、坍塌、停业”等后果误判为 FireEvent。
4. 优先形成 Hazard -> FireEvent -> Consequence 的分层结构。
5. 若文本没有明确后果，可以不强行补造 Consequence 节点。
6. edges 中的 source / target 必须引用 nodes 中的 standard_term，且节点类型必须一致。
7. relation 只能使用 LEADS_TO、CAUSES、RESULTS_IN 三种之一。
8. LEADS_TO 只能用于 Hazard -> FireEvent，绝对不要用于 FireEvent -> FireEvent。
9. 如果 source_type 和 target_type 都是 FireEvent，relation 必须使用 CAUSES。
10. 如果 target_type 是 Consequence，优先使用 RESULTS_IN，不要把 FireEvent -> Consequence 写成 LEADS_TO。

## 输出格式：
必须严格按照以下 JSON 格式输出，不要包含任何其他文字：

```json
{
  "nodes": [
    {
      "node_type": "Hazard",
      "description": "电线绝缘层老化破损",
      "standard_term": "绝缘层老化破损",
      "context": "配电箱内线路长期老化失修"
    }
  ],
  "edges": [
    {
      "source": "绝缘层老化破损",
      "source_type": "Hazard",
      "target": "电气短路",
      "target_type": "FireEvent",
      "relation": "LEADS_TO",
      "confidence": 0.92,
      "context": "绝缘失效后发生短路"
    }
  ]
}
```

## 注意事项：
- description 要具体，standard_term 要简洁。
- confidence 是 0 到 1 之间的数值。
- 只输出 JSON，不要附加解释说明。
- 确保 JSON 可被程序直接解析。"""

    def _create_few_shot_examples(self) -> List[Dict[str, Any]]:
        """创建Few-Shot学习示例"""
        return [
            {
                "input": """事故经过：2023年3月15日，某工厂配电箱发生故障，电线绝缘层破损导致短路，产生电弧引燃了附近的包装材料，火势迅速蔓延。
原因分析：电气线路老化是主要原因，安全检查不到位是管理原因。结果造成仓库部分货物烧毁，直接经济损失50万元。""",
                "output": {
                    "nodes": [
                        {
                            "node_type": "Hazard",
                            "description": "电气线路老化",
                            "standard_term": "电气线路老化",
                            "context": "长期使用导致线路性能下降"
                        },
                        {
                            "node_type": "Hazard",
                            "description": "安全检查不到位",
                            "standard_term": "安全检查不到位",
                            "context": "缺乏定期检查导致隐患未及时发现"
                        },
                        {
                            "node_type": "Hazard",
                            "description": "电线绝缘层破损",
                            "standard_term": "绝缘层破损",
                            "context": "配电箱内电线绝缘失效"
                        },
                        {
                            "node_type": "FireEvent",
                            "description": "电路短路",
                            "standard_term": "电路短路",
                            "context": "绝缘层破损后发生短路"
                        },
                        {
                            "node_type": "FireEvent",
                            "description": "产生电弧",
                            "standard_term": "产生电弧",
                            "context": "短路时产生高温电弧"
                        },
                        {
                            "node_type": "FireEvent",
                            "description": "引燃包装材料",
                            "standard_term": "引燃包装材料",
                            "context": "电弧高温引燃附近可燃物"
                        },
                        {
                            "node_type": "FireEvent",
                            "description": "火势迅速蔓延",
                            "standard_term": "火势蔓延",
                            "context": "可燃材料助长火势扩散"
                        },
                        {
                            "node_type": "Consequence",
                            "description": "仓库部分货物烧毁",
                            "standard_term": "货物烧毁",
                            "context": "火灾造成仓库存货受损"
                        },
                        {
                            "node_type": "Consequence",
                            "description": "直接经济损失50万元",
                            "standard_term": "经济损失50万元",
                            "context": "事故造成直接经济损失"
                        }
                    ],
                    "edges": [
                        {
                            "source": "电气线路老化",
                            "source_type": "Hazard",
                            "target": "绝缘层破损",
                            "target_type": "Hazard",
                            "relation": "CAUSES",
                            "confidence": 0.91,
                            "context": "线路老化导致绝缘性能下降"
                        },
                        {
                            "source": "安全检查不到位",
                            "source_type": "Hazard",
                            "target": "电气线路老化",
                            "target_type": "Hazard",
                            "relation": "CAUSES",
                            "confidence": 0.78,
                            "context": "检查不到位使线路老化隐患长期存在"
                        },
                        {
                            "source": "绝缘层破损",
                            "source_type": "Hazard",
                            "target": "电路短路",
                            "target_type": "FireEvent",
                            "relation": "LEADS_TO",
                            "confidence": 0.95,
                            "context": "绝缘失效引发短路"
                        },
                        {
                            "source": "电路短路",
                            "source_type": "FireEvent",
                            "target": "产生电弧",
                            "target_type": "FireEvent",
                            "relation": "CAUSES",
                            "confidence": 0.92,
                            "context": "短路会产生高温电弧"
                        },
                        {
                            "source": "产生电弧",
                            "source_type": "FireEvent",
                            "target": "引燃包装材料",
                            "target_type": "FireEvent",
                            "relation": "CAUSES",
                            "confidence": 0.88,
                            "context": "电弧引燃周边可燃物"
                        },
                        {
                            "source": "引燃包装材料",
                            "source_type": "FireEvent",
                            "target": "火势蔓延",
                            "target_type": "FireEvent",
                            "relation": "CAUSES",
                            "confidence": 0.84,
                            "context": "起火后火势持续扩散"
                        },
                        {
                            "source": "火势蔓延",
                            "source_type": "FireEvent",
                            "target": "货物烧毁",
                            "target_type": "Consequence",
                            "relation": "RESULTS_IN",
                            "confidence": 0.90,
                            "context": "火势蔓延造成仓库存货烧毁"
                        },
                        {
                            "source": "火势蔓延",
                            "source_type": "FireEvent",
                            "target": "经济损失50万元",
                            "target_type": "Consequence",
                            "relation": "RESULTS_IN",
                            "confidence": 0.86,
                            "context": "事故造成直接经济损失"
                        }
                    ]
                }
            }
        ]
    
    async def extract_structured_event_graph(
        self,
        text: str,
        config: Optional[ExtractionConfig] = None
    ) -> LayeredExtractionResult:
        """从文本中提取分层事件图"""
        if not self.client:
            await self.initialize()
        
        if config is None:
            config = ExtractionConfig(
                llm_model=self.model,
                temperature=0.1,
                max_tokens=3000,
                extraction_prompt=self.system_prompt
            )
        
        try:
            messages = self._build_messages(text, config)
            
            start_time = datetime.now()
            response = await self.client.chat.completions.create(
                model=config.llm_model,
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                response_format={"type": "json_object"}
            )
            end_time = datetime.now()
            
            llm_response = LLMResponse(
                content=response.choices[0].message.content,
                usage=response.usage.model_dump() if hasattr(response.usage, 'model_dump') else dict(response.usage),
                model=response.model,
                finish_reason=response.choices[0].finish_reason,
                response_time=(end_time - start_time).total_seconds()
            )
            
            layered_result = self._parse_layered_result(llm_response.content)
            logger.info(
                f"成功提取分层图谱：{len(layered_result.nodes)} 个节点，"
                f"{len(layered_result.edges)} 条关系，耗时 {llm_response.response_time:.2f}秒"
            )
            return layered_result
        except Exception as e:
            logger.error(f"分层事件图提取失败: {e}")
            raise
    
    async def extract_event_chains(
        self,
        text: str,
        config: Optional[ExtractionConfig] = None
    ) -> List[EventChainCreate]:
        """兼容旧接口：从分层抽取结果映射为事件链"""
        layered_result = await self.extract_structured_event_graph(text, config)
        event_chains = layered_result.to_event_chains()
        logger.info(f"从分层结果映射出 {len(event_chains)} 个事件链")
        return event_chains
    
    def _build_messages(self, text: str, config: ExtractionConfig) -> List[Dict[str, str]]:
        """构建LLM消息"""
        messages = [
            {"role": "system", "content": config.extraction_prompt}
        ]
        
        for example in config.few_shot_examples or self.few_shot_examples:
            messages.append({
                "role": "user", 
                "content": f"请分析以下火灾事故文本：\n\n{example['input']}"
            })
            messages.append({
                "role": "assistant", 
                "content": json.dumps(example['output'], ensure_ascii=False, indent=2)
            })
        
        messages.append({
            "role": "user",
            "content": f"请分析以下火灾事故文本：\n\n{text}"
        })
        
        return messages
    
    def _parse_layered_result(self, llm_output: str) -> LayeredExtractionResult:
        """解析LLM输出的分层结果"""
        try:
            data = json.loads(llm_output)
            if "nodes" not in data or "edges" not in data:
                raise ValueError("LLM输出格式错误：缺少nodes或edges字段")

            data = self._normalize_layered_result(data)
            nodes = [ExtractedNode(**node_data) for node_data in data["nodes"]]
            edges = [ExtractedEdge(**edge_data) for edge_data in data["edges"] if not edge_data.get("_invalid")]
            self._validate_edge_node_references(nodes, edges)
            return LayeredExtractionResult(nodes=nodes, edges=edges)
        except json.JSONDecodeError as e:
            logger.error(f"LLM输出JSON解析失败: {e}")
            raise ValueError(f"LLM输出不是有效的JSON格式: {e}")
        except ValidationError as e:
            logger.error(f"分层抽取结果验证失败: {e}")
            raise ValueError(f"分层抽取结果格式验证失败: {e}")
        except Exception as e:
            logger.error(f"分层抽取结果解析失败: {e}")
            raise

    def _normalize_layered_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """对LLM输出做轻量归一化，修复常见但语义明确的关系错误。"""
        normalized = deepcopy(data)
        edges = normalized.get("edges")
        if not isinstance(edges, list):
            return normalized

        for edge in edges:
            if not isinstance(edge, dict):
                continue
            self._normalize_edge_relation(edge)

        return normalized

    def _normalize_edge_relation(self, edge: Dict[str, Any]) -> None:
        """归一化单条边的关系类型。"""
        source_type = edge.get("source_type", "")
        target_type = edge.get("target_type", "")
        relation = edge.get("relation", "")

        if not source_type or not target_type or not relation:
            return

        if (
            source_type == ExtractedNodeType.FIRE_EVENT.value
            and target_type == ExtractedNodeType.FIRE_EVENT.value
            and relation == ExtractedRelationType.LEADS_TO.value
        ):
            edge["relation"] = ExtractedRelationType.CAUSES.value
            logger.warning(
                "检测到非法关系 FireEvent-[LEADS_TO]->FireEvent，已自动纠正为 CAUSES: %s -> %s",
                edge.get("source", "<unknown>"),
                edge.get("target", "<unknown>"),
            )
            return

        if target_type == ExtractedNodeType.CONSEQUENCE.value and relation == ExtractedRelationType.LEADS_TO.value:
            edge["relation"] = ExtractedRelationType.RESULTS_IN.value
            logger.warning(
                "检测到 Consequence 目标边误用 LEADS_TO，已自动纠正为 RESULTS_IN: %s -> %s",
                edge.get("source", "<unknown>"),
                edge.get("target", "<unknown>"),
            )
            return

        if (
            source_type == ExtractedNodeType.HAZARD.value
            and target_type == ExtractedNodeType.FIRE_EVENT.value
            and relation == ExtractedRelationType.RESULTS_IN.value
        ):
            edge["relation"] = ExtractedRelationType.LEADS_TO.value
            logger.warning(
                "检测到 Hazard->FireEvent 误用 RESULTS_IN，已自动纠正为 LEADS_TO: %s -> %s",
                edge.get("source", "<unknown>"),
                edge.get("target", "<unknown>"),
            )
            return

        if source_type == ExtractedNodeType.CONSEQUENCE.value:
            edge["_invalid"] = True
            logger.warning(
                "检测到 Consequence 作为源节点的非法关系，已自动过滤: %s -> %s",
                edge.get("source", "<unknown>"),
                edge.get("target", "<unknown>"),
            )
            return

        if target_type == ExtractedNodeType.HAZARD.value:
            edge["relation"] = ExtractedRelationType.RESULTS_IN.value
            logger.warning(
                "检测到 Hazard 作为目标节点的非法关系，已自动纠正为 RESULTS_IN: %s -> %s",
                edge.get("source", "<unknown>"),
                edge.get("target", "<unknown>"),
            )
            return

    def _validate_edge_node_references(
        self,
        nodes: List[ExtractedNode],
        edges: List[ExtractedEdge]
    ) -> None:
        """校验边引用的节点存在且类型一致"""
        node_index = {node.standard_term: node.node_type for node in nodes}
        
        for edge in edges:
            source_type = node_index.get(edge.source)
            target_type = node_index.get(edge.target)
            
            if source_type is None:
                raise ValueError(f"关系源节点不存在: {edge.source}")
            if target_type is None:
                raise ValueError(f"关系目标节点不存在: {edge.target}")
            if source_type != edge.source_type:
                raise ValueError(
                    f"关系源节点类型不匹配: {edge.source}, 期望 {source_type}, 实际 {edge.source_type}"
                )
            if target_type != edge.target_type:
                raise ValueError(
                    f"关系目标节点类型不匹配: {edge.target}, 期望 {target_type}, 实际 {edge.target_type}"
                )
    
    async def test_connection(self) -> Dict[str, Any]:
        """测试LLM API连接"""
        if not self.client:
            await self.initialize()
        
        try:
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
        
        keywords = ["火灾", "起火", "燃烧", "事故", "原因", "经过"]
        keyword_count = sum(1 for keyword in keywords if keyword in text)
        
        if keyword_count < 2:
            return {
                "suitable": False,
                "reason": "文本缺少火灾事故相关关键词",
                "suggestions": ["请确认文本包含火灾事故描述、原因分析或经过信息"]
            }
        
        return {
            "suitable": True,
            "reason": "文本适合进行分层事件链抽取",
            "suggestions": [
                "建议保留事故经过、原因分析、调查结果等章节信息",
                "可用于构建 Hazard -> FireEvent -> Consequence 图谱"
            ]
        }


llm_service = LLMService()
