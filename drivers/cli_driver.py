"""
CLI外壳驱动 - 命令行界面
LLM 连接使用 openai SDK（兼容 Ollama 和 OpenAI）
"""

import sys
from openai import OpenAI
from core.agent import DriverInterface


class CLIDriver(DriverInterface):
    """命令行驱动"""

    def __init__(self, llm_config: dict = None):
        self.llm_config = llm_config or {
            "type": "ollama",
            "host": "http://localhost:11434",
            "model": "qwen2.5:7b",
        }
        self.client = self._create_client()
        self.model = self.llm_config.get("model", "qwen2.5:7b")

    def _create_client(self) -> OpenAI:
        """创建 OpenAI 兼容客户端"""
        host = self.llm_config.get("host", "http://localhost:11434")
        api_key = self.llm_config.get("api_key", "ollama")  # Ollama 不需要真实 key

        return OpenAI(base_url=f"{host}/v1", api_key=api_key)

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
        """调用 LLM — 使用 openai SDK"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ LLM调用失败: {str(e)}"
