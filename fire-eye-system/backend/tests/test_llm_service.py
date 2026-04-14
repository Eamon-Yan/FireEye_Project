"""
LLM服务测试
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch

from app.services.llm_service import LLMService, llm_service
from app.schemas.extraction import ExtractionConfig
from app.schemas.event_chain import EventChainCreate, RelationType


class TestLLMService:
    """LLM服务测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.service = LLMService()
    
    def test_initialization(self):
        """测试服务初始化"""
        assert self.service.model == "deepseek-chat"
        assert self.service.base_url == "https://api.deepseek.com"
        assert self.service.system_prompt is not None
        assert len(self.service.few_shot_examples) > 0
    
    def test_system_prompt_creation(self):
        """测试系统提示词创建"""
        prompt = self.service._create_fire_expert_prompt()
        
        assert "火灾事故调查专家" in prompt
        assert "Hazard -> FireEvent -> Consequence" in prompt
        assert "JSON" in prompt
        assert "LEADS_TO 只能用于 Hazard -> FireEvent" in prompt
        assert "FireEvent，relation 必须使用 CAUSES" in prompt
    
    def test_few_shot_examples_creation(self):
        """测试Few-Shot示例创建"""
        examples = self.service._create_few_shot_examples()
        
        assert len(examples) > 0
        assert "input" in examples[0]
        assert "output" in examples[0]
        assert "nodes" in examples[0]["output"]
        assert "edges" in examples[0]["output"]

    def test_normalize_fire_event_leads_to_fire_event(self):
        """测试将 FireEvent 到 FireEvent 的 LEADS_TO 纠正为 CAUSES"""
        data = {
            "nodes": [
                {"node_type": "FireEvent", "description": "短路", "standard_term": "短路", "context": ""},
                {"node_type": "FireEvent", "description": "电弧", "standard_term": "电弧", "context": ""},
            ],
            "edges": [
                {
                    "source": "短路",
                    "source_type": "FireEvent",
                    "target": "电弧",
                    "target_type": "FireEvent",
                    "relation": "LEADS_TO",
                    "confidence": 0.9,
                    "context": "短路后形成电弧",
                }
            ],
        }

        normalized = self.service._normalize_layered_result(data)

        assert normalized["edges"][0]["relation"] == "CAUSES"

    def test_normalize_consequence_leads_to_results_in(self):
        """测试将指向 Consequence 的 LEADS_TO 纠正为 RESULTS_IN"""
        data = {
            "nodes": [
                {"node_type": "FireEvent", "description": "火势蔓延", "standard_term": "火势蔓延", "context": ""},
                {"node_type": "Consequence", "description": "货物烧毁", "standard_term": "货物烧毁", "context": ""},
            ],
            "edges": [
                {
                    "source": "火势蔓延",
                    "source_type": "FireEvent",
                    "target": "货物烧毁",
                    "target_type": "Consequence",
                    "relation": "LEADS_TO",
                    "confidence": 0.88,
                    "context": "火势扩大造成货损",
                }
            ],
        }

        normalized = self.service._normalize_layered_result(data)

        assert normalized["edges"][0]["relation"] == "RESULTS_IN"

    def test_parse_layered_result_recovers_common_invalid_relations(self):
        """测试解析层可修复常见非法关系并生成结果"""
        llm_output = json.dumps(
            {
                "nodes": [
                    {"node_type": "Hazard", "description": "导线老化", "standard_term": "导线老化", "context": ""},
                    {"node_type": "FireEvent", "description": "短路", "standard_term": "短路", "context": ""},
                    {"node_type": "FireEvent", "description": "电弧", "standard_term": "电弧", "context": ""},
                    {"node_type": "Consequence", "description": "货物烧毁", "standard_term": "货物烧毁", "context": ""},
                ],
                "edges": [
                    {
                        "source": "导线老化",
                        "source_type": "Hazard",
                        "target": "短路",
                        "target_type": "FireEvent",
                        "relation": "RESULTS_IN",
                        "confidence": 0.93,
                        "context": "隐患导向短路",
                    },
                    {
                        "source": "短路",
                        "source_type": "FireEvent",
                        "target": "电弧",
                        "target_type": "FireEvent",
                        "relation": "LEADS_TO",
                        "confidence": 0.91,
                        "context": "短路形成电弧",
                    },
                    {
                        "source": "电弧",
                        "source_type": "FireEvent",
                        "target": "货物烧毁",
                        "target_type": "Consequence",
                        "relation": "LEADS_TO",
                        "confidence": 0.86,
                        "context": "电弧引发后果",
                    },
                ],
            },
            ensure_ascii=False,
        )

        result = self.service._parse_layered_result(llm_output)

        assert len(result.nodes) == 4
        assert len(result.edges) == 3
        assert result.edges[0].relation == "LEADS_TO"
        assert result.edges[1].relation == "CAUSES"
        assert result.edges[2].relation == "RESULTS_IN"
    
    @pytest.mark.asyncio
    async def test_initialize_without_api_key(self):
        """测试无API密钥时的初始化"""
        service = LLMService()
        service.api_key = None
        
        with pytest.raises(ValueError, match="OPENAI_API_KEY未设置"):
            await service.initialize()
    
    @pytest.mark.asyncio
    @patch('app.services.llm_service.AsyncOpenAI')
    async def test_initialize_with_api_key(self, mock_openai):
        """测试有API密钥时的初始化"""
        service = LLMService()
        service.api_key = "test-key"
        
        await service.initialize()
        
        mock_openai.assert_called_once_with(
            api_key="test-key",
            base_url="https://api.deepseek.com"
        )
        assert service.client is not None
    
    def test_build_messages(self):
        """测试消息构建"""
        config = ExtractionConfig(
            extraction_prompt="测试提示词",
            few_shot_examples=[]
        )
        
        messages = self.service._build_messages("测试文本", config)
        
        assert len(messages) >= 2  # 至少包含系统消息和用户消息
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "测试提示词"
        assert messages[-1]["role"] == "user"
        assert "测试文本" in messages[-1]["content"]
    
    @pytest.mark.asyncio
    async def test_analyze_text_quality_short_text(self):
        """测试分析过短文本的质量"""
        result = await self.service.analyze_text_quality("短文本")
        
        assert result["suitable"] is False
        assert "过短" in result["reason"]
        assert len(result["suggestions"]) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_text_quality_no_fire_content(self):
        """测试分析无火灾内容的文本质量"""
        text = "这是一个关于天气的长文本，描述了今天和未来几天的天气情况，阳光明媚，温度适宜，空气清新，风力较小，非常适合外出活动和城市散步。"
        result = await self.service.analyze_text_quality(text)
        
        assert result["suitable"] is False
        assert "缺少火灾事故相关关键词" in result["reason"]
    
    @pytest.mark.asyncio
    async def test_analyze_text_quality_good_text(self):
        """测试分析优质文本"""
        text = "火灾事故调查报告显示，2023年某仓库发生火灾，原因是电气线路老化导致短路起火，随后火势迅速蔓延并造成货物烧毁，调查记录包含事故经过、原因分析和现场处置情况。"
        result = await self.service.analyze_text_quality(text)
        
        assert result["suitable"] is True
        assert "适合进行分层事件链抽取" in result["reason"]
    
    @pytest.mark.asyncio
    @patch('app.services.llm_service.AsyncOpenAI')
    async def test_test_connection_success(self, mock_openai):
        """测试连接成功"""
        # 模拟成功的API响应
        mock_response = Mock()
        mock_response.model = "deepseek-chat"
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "连接测试成功"
        mock_response.usage = {"prompt_tokens": 10, "completion_tokens": 5}
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        service = LLMService()
        service.api_key = "test-key"
        
        result = await service.test_connection()
        
        assert result["status"] == "success"
        assert result["model"] == "deepseek-chat"
        assert result["response"] == "连接测试成功"
    
    @pytest.mark.asyncio
    @patch('app.services.llm_service.AsyncOpenAI')
    async def test_test_connection_failure(self, mock_openai):
        """测试连接失败"""
        mock_client = AsyncMock()
        mock_client.chat.completions.create.side_effect = Exception("API错误")
        mock_openai.return_value = mock_client
        
        service = LLMService()
        service.api_key = "test-key"
        
        result = await service.test_connection()
        
        assert result["status"] == "failed"
        assert "API错误" in result["error"]
    
    @pytest.mark.asyncio
    @patch('app.services.llm_service.AsyncOpenAI')
    async def test_extract_event_chains_success(self, mock_openai):
        """测试成功提取事件链"""
        # 模拟LLM响应
        mock_response = Mock()
        mock_response.model = "deepseek-chat"
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "nodes": [
                {
                    "node_type": "Hazard",
                    "description": "电线老化",
                    "standard_term": "电线老化",
                    "context": "电气设备老化"
                },
                {
                    "node_type": "FireEvent",
                    "description": "短路起火",
                    "standard_term": "短路起火",
                    "context": "线路故障后起火"
                }
            ],
            "edges": [
                {
                    "source": "电线老化",
                    "source_type": "Hazard",
                    "target": "短路起火",
                    "target_type": "FireEvent",
                    "relation": "LEADS_TO",
                    "confidence": 0.9,
                    "context": "电气设备老化导致"
                }
            ]
        }, ensure_ascii=False)
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = {"prompt_tokens": 100, "completion_tokens": 50}
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        service = LLMService()
        service.api_key = "test-key"
        
        text = "火灾事故：电线老化导致短路起火"
        event_chains = await service.extract_event_chains(text)
        
        assert len(event_chains) == 1
        assert event_chains[0].source == "电线老化"
        assert event_chains[0].relation == RelationType.TRIGGERS
        assert event_chains[0].target == "短路起火"
    
class TestGlobalService:
    """全局服务实例测试"""
    
    def test_llm_service_instance(self):
        """测试全局LLM服务实例"""
        assert llm_service is not None
        assert isinstance(llm_service, LLMService)
        assert hasattr(llm_service, 'client')
        assert hasattr(llm_service, 'system_prompt')
