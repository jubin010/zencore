"""
LLM模块 - 支持多种大语言模型后端
"""

import requests
import json
from typing import List, Dict, Optional


class BaseLLM:
    """LLM基类"""
    
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model
    
    def chat(self, messages: List[Dict]) -> str:
        """发送对话请求"""
        raise NotImplementedError


class OllamaLLM(BaseLLM):
    """Ollama本地LLM"""
    
    def chat(self, messages: List[Dict]) -> str:
        """调用Ollama API"""
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result.get('message', {}).get('content', '（无回复）')
            
        except requests.exceptions.ConnectionError:
            return "⚠️ 无法连接到Ollama服务，请确保Ollama正在运行"
        except requests.exceptions.Timeout:
            return "⚠️ Ollama响应超时"
        except Exception as e:
            return f"⚠️ LLM调用失败: {str(e)}"


class OpenAILLM(BaseLLM):
    """OpenAI兼容API"""
    
    def __init__(self, base_url: str, model: str, api_key: str = None):
        super().__init__(base_url, model)
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
    
    def chat(self, messages: List[Dict]) -> str:
        """调用OpenAI兼容API"""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": self.model,
            "messages": messages
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result.get('choices', [{}])[0].get('message', {}).get('content', '（无回复）')
            
        except Exception as e:
            return f"⚠️ LLM调用失败: {str(e)}"


class LLMFactory:
    """LLM工厂类"""
    
    @staticmethod
    def create(provider: str, **kwargs) -> BaseLLM:
        """
        创建LLM实例
        
        Args:
            provider: 提供商名称 (ollama, openai, deepseek等)
            **kwargs: 其他参数
        """
        providers = {
            'ollama': OllamaLLM,
            'openai': OpenAILLM,
        }
        
        if provider.lower() not in providers:
            raise ValueError(f"不支持的LLM提供商: {provider}")
        
        return providers[provider.lower()](**kwargs)
