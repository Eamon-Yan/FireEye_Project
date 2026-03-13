"""
LLM服务测试
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.llm_service import LLMService, llm_service
from app.schemas.extraction import ExtractionConfig, LLMResponse
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
        assert "事件链" in prompt
        assert "JSON" in prompt
        assert "导致" in prompt
        assert "促进" in prompt
    
    def test_few_shot_examples_creation(self):
        """测试Few-Shot示例创建"""
        examples = self.service._create_few_shot_examples()
        
        assert len(examples) > 0
        assert "input" in examples[0]
        assert "output" in examples[0]
        assert "event_chains" in examples[0]["output"]
    
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
    
    def test_parse_event_chains_valid_json(self):
        """测试解析有效的事件链JSON"""
        llm_output = json.dumps({
            "event_chains": [
                {
                    "source": "电线老化",
                    "relation": "导致",
                    "target": "短路起火",
                    "confidence": 0.9,
                    "context": "电气设备老化"
                }
            ]
        }, ensure_ascii=False)
        
        event_chains = self.service._parse_event_chains(llm_output)
        
        assert len(event_chains) == 1
        assert event_chains[0].source == "电线老化"
        assert event_chains[0].relation == RelationType.CAUSES
        assert event_chains[0].target == "短路起火"
        assert event_chains[0].confidence == 0.9
        assert event_chains[0].context == "电气设备老化"
    
    def test_parse_event_chains_invalid_json(self):
        """测试解析无效JSON"""
        llm_output = "这不是有效的JSON"
        
        with pytest.raises(ValueError, match="LLM输出不是有效的JSON格式"):
            self.service._parse_event_chains(llm_output)
    
    def test_parse_event_chains_missing_field(self):
        """测试解析缺少字段的JSON"""
        llm_output = json.dumps({
            "wrong_field": []
        })
        
        with pytest.raises(ValueError, match="缺少event_chains字段"):
            self.service._parse_event_chains(llm_output)
    
    def test_parse_event_chains_invalid_relation(self):
        """测试解析无效关系类型"""
        llm_output = json.dumps({
            "event_chains": [
                {
                    "source": "测试源",
                    "relation": "无效关系",
                    "target": "测试目标",
                    "confidence": 0.8,
                    "context": "测试上下文"
                }
            ]
        }, ensure_ascii=False)
        
        # 应该使用默认关系类型
        event_chains = self.service._parse_event_chains(llm_output)
        assert len(event_chains) == 1
        assert event_chains[0].relation == RelationType.CAUSES
    
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
        text = "这是一个关于天气的长文本，描述了今天的天气情况，阳光明媚，温度适宜，非常适合外出活动。"
        result = await self.service.analyze_text_quality(text)
        
        assert result["suitable"] is False
        assert "不包含火灾相关内容" in result["reason"]
    
    @pytest.mark.asyncio
    async def test_analyze_text_quality_good_text(self):
        """测试分析优质文本"""
        text = "火灾事故调查报告：2023年发生火灾，原因是电气线路老化导致短路起火，火势迅速蔓延。"
        result = await self.service.analyze_text_quality(text)
        
        assert result["suitable"] is True
        assert "适合进行事件链提取" in result["reason"]
    
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
            "event_chains": [
                {
                    "source": "电线老化",
                    "relation": "导致", 
                    "target": "短路起火",
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
        assert event_chains[0].relation == RelationType.CAUSES
        assert event_chains[0].target == "短路起火"
    
    @pytest.mark.asyncio
    async def test_batch_extract_event_chains(self):
        """测试批量提取事件链"""
        service = LLMService()
        
        # 模拟extract_event_chains方法
        async def mock_extract(text, config=None):
            return [EventChainCreate(
                source="测试源",
                relation=RelationType.CAUSES,
                target="测试目标",
                confidence=0.8,
                context="测试上下文"
            )]
        
        service.extract_event_chains = mock_extract
        
        texts = ["文本1", "文本2"]
        results = await service.batch_extract_event_chains(texts)
        
        assert len(results) == 2
        assert len(results[0]) == 1
        assert len(results[1]) == 1


class TestGlobalService:
    """全局服务实例测试"""
    
    def test_llm_service_instance(self):
        """测试全局LLM服务实例"""
        assert llm_service is not None
        assert isinstance(llm_service, LLMService)
        assert hasattr(llm_service, 'client')
        assert hasattr(llm_service, 'system_prompt')