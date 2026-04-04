"""
CLI外壳驱动 - 命令行界面
通过 api_key 自动判断模型类别：
- api_key 为空或 "ollama" -> 使用 ollama 原生包
- 其他 -> 使用 openai SDK

支持思考模式（thinking）：自动剥离 <think> 标签，打印思考过程
"""

import re
import sys
from core.agent import DriverInterface


class CLIDriver(DriverInterface):
    """命令行驱动"""

    def __init__(self, llm_config: dict = None):
        self.llm_config = llm_config or {
            "host": "http://localhost:11434",
            "model": "qwen3.5:9b",
            "api_key": "ollama",
            "thinking": False,
        }
        self.host = self.llm_config.get("host", "http://localhost:11434")
        self.model = self.llm_config.get("model", "qwen3.5:9b")
        self.api_key = self.llm_config.get("api_key", "")
        self.thinking = self.llm_config.get("thinking", False)
        self._client = None

    def _get_client(self):
        """懒加载客户端，根据 api_key 自动路由"""
        if self._client is None:
            if not self.api_key or self.api_key.lower() == "ollama":
                import ollama
                self._client = ollama.Client(host=self.host)
            else:
                from openai import OpenAI
                self._client = OpenAI(base_url=f"{self.host}/v1", api_key=self.api_key)
        return self._client

    def _extract_thinking(self, content: str) -> tuple:
        """提取思考过程，返回 (thinking, answer)"""
        pattern = r'<think>(.*?)</think>\s*(.*)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        return "", content

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
                response = client.chat(
                    model=self.model,
                    messages=messages,
                    think=self.thinking,
                )
                content = response["message"]["content"]
            else:
                extra_body = {}
                if self.thinking:
                    extra_body["thinking"] = True
                
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    extra_body=extra_body,
                )
                content = response.choices[0].message.content

            # 处理思考模式：剥离 <think> 标签，打印思考过程
            if self.thinking:
                thinking, answer = self._extract_thinking(content)
                if thinking:
                    print(f"\n💭 思考过程:\n{thinking}\n")
                    print(f"{'─' * 40}")
                return answer

            return content

        except Exception as e:
            return f"❌ LLM调用失败: {str(e)}"
