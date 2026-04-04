"""
CLI外壳驱动 - 命令行界面
Ollama 用 ollama 包，OpenAI 用 openai 包
"""

import sys
from core.agent import DriverInterface


class CLIDriver(DriverInterface):
    """命令行驱动"""

    def __init__(self, llm_config: dict = None):
        self.llm_config = llm_config or {
            "type": "ollama",
            "host": "http://localhost:11434",
            "model": "qwen3.5:9b",
        }
        self.model = self.llm_config.get("model", "qwen3.5:9b")
        self._client = None

    def _get_client(self):
        """懒加载客户端"""
        if self._client is None:
            llm_type = self.llm_config.get("type", "ollama")
            if llm_type == "ollama":
                import ollama
                host = self.llm_config.get("host", "http://localhost:11434")
                self._client = ollama.Client(host=host)
            else:
                from openai import OpenAI
                host = self.llm_config.get("host", "http://localhost:11434")
                api_key = self.llm_config.get("api_key", "")
                self._client = OpenAI(base_url=f"{host}/v1", api_key=api_key)
        return self._client

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
        """调用 LLM — 根据类型自动选择 SDK"""
        try:
            llm_type = self.llm_config.get("type", "ollama")
            client = self._get_client()

            if llm_type == "ollama":
                response = client.chat(model=self.model, messages=messages)
                return response["message"]["content"]
            else:
                response = client.chat.completions.create(
                    model=self.model, messages=messages, temperature=0.7
                )
                return response.choices[0].message.content
        except Exception as e:
            return f"❌ LLM调用失败: {str(e)}"
