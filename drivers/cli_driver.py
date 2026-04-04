"""
CLI外壳驱动 - 命令行界面
通过 api_key 自动判断模型类别：
- api_key 为空或 "ollama" -> 使用 ollama 原生包
- 其他 -> 使用 openai SDK

支持思考模式：
- Ollama: 使用 response.message.thinking
- OpenAI 兼容 (MiniMax): 使用 reasoning_details 字段
"""

import sys
from core.agent import DriverInterface


class CLIDriver(DriverInterface):
    """命令行驱动"""

    def __init__(self, model_config: dict = None):
        self.model_config = model_config or {
            "name": "默认模型",
            "host": "http://localhost:11434",
            "model": "qwen3.5:9b",
            "api_key": "ollama",
            "thinking": False,
        }
        self.name = self.model_config.get("name", "未知模型")
        self.host = self.model_config.get("host", "http://localhost:11434")
        self.model = self.model_config.get("model", "qwen3.5:9b")
        self.api_key = self.model_config.get("api_key", "")
        self.thinking = self.model_config.get("thinking", False)
        self.thinking_mode = self.model_config.get("thinking_mode", "")
        self._client = None

    def switch_model(self, model_config: dict):
        """切换模型配置"""
        self.model_config = model_config
        self.name = model_config.get("name", "未知模型")
        self.host = model_config.get("host", "http://localhost:11434")
        self.model = model_config.get("model", "qwen3.5:9b")
        self.api_key = model_config.get("api_key", "")
        self.thinking = model_config.get("thinking", False)
        self.thinking_mode = model_config.get("thinking_mode", "")
        self._client = None

    def _get_client(self):
        """懒加载客户端，根据 api_key 自动路由"""
        if self._client is None:
            if not self.api_key or self.api_key.lower() == "ollama":
                import ollama
                self._client = ollama.Client(host=self.host)
            else:
                from openai import OpenAI
                self._client = OpenAI(base_url=self.host, api_key=self.api_key)
        return self._client

    def _extract_thinking_from_openai(self, message) -> str:
        """从 OpenAI 兼容响应中提取思考内容（MiniMax reasoning_details）"""
        if hasattr(message, 'reasoning_details') and message.reasoning_details:
            parts = []
            for detail in message.reasoning_details:
                if isinstance(detail, dict) and "text" in detail:
                    parts.append(detail["text"])
                elif hasattr(detail, 'text'):
                    parts.append(detail.text)
            return "\n".join(parts)
        return ""

    def send_message(self, content: str) -> None:
        print(content)

    def send_image(self, path: str) -> None:
        print(f"[图片: {path}]")

    def send_file(self, path: str) -> None:
        print(f"[文件: {path}]")

    def get_input(self, prompt: str = "") -> str:
        try:
            return input(prompt)
        except EOFError:
            return ""

    def show_loading(self, message: str = "处理中..."):
        print(f"⏳ {message}...")
        class LoadingCtx:
            def __enter__(self): return self
            def __exit__(self, *args): print("✅ 完成")
        return LoadingCtx()

    def toast(self, message: str, duration: int = 3) -> None:
        print(f"📢 {message}")

    def set_title(self, title: str) -> None:
        pass

    def call_llm(self, messages: list) -> str:
        """调用 LLM — 根据 api_key 自动选择 SDK"""
        try:
            client = self._get_client()
            
            if not self.api_key or self.api_key.lower() == "ollama":
                # Ollama 原生包
                response = client.chat(
                    model=self.model,
                    messages=messages,
                    think=self.thinking,
                )
                
                if self.thinking and hasattr(response.message, 'thinking') and response.message.thinking:
                    thinking = response.message.thinking
                    answer = response.message.content
                    print(f"\n💭 思考过程:\n{thinking}\n")
                    print(f"{'─' * 40}")
                    return answer
                
                return response.message.content
                
            else:
                # OpenAI 兼容接口
                extra_body = {}
                if self.thinking:
                    if self.thinking_mode == "reasoning_split":
                        extra_body["reasoning_split"] = True
                    else:
                        extra_body["thinking"] = True
                
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    extra_body=extra_body,
                )
                
                message = response.choices[0].message
                
                # 处理 MiniMax reasoning_split 模式
                if self.thinking and self.thinking_mode == "reasoning_split":
                    thinking = self._extract_thinking_from_openai(message)
                    if thinking:
                        print(f"\n💭 思考过程:\n{thinking}\n")
                        print(f"{'─' * 40}")
                    return message.content
                
                # 处理标准 thinking 模式
                if self.thinking and hasattr(message, 'thinking') and message.thinking:
                    thinking = message.thinking
                    print(f"\n💭 思考过程:\n{thinking}\n")
                    print(f"{'─' * 40}")
                    return message.content

                return message.content

        except Exception as e:
            return f"❌ LLM调用失败: {str(e)}"
