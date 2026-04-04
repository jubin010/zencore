"""
CLI外壳驱动 - 命令行界面
LLM 配置属于外壳，由驱动决定连接哪个 LLM
"""

import sys
import json
import urllib.request
import urllib.error
from core.agent import DriverInterface


class CLIDriver(DriverInterface):
    """命令行驱动"""

    def __init__(self, llm_config: dict = None):
        self.history = []
        # LLM 配置 — 外壳的事
        self.llm_config = llm_config or {
            "type": "ollama",
            "host": "http://localhost:11434",
            "model": "qwen2.5:7b",
        }

    def send_message(self, content: str) -> None:
        """打印消息"""
        print(content)

    def send_image(self, path: str) -> None:
        """打印图片路径"""
        print(f"[图片: {path}]")

    def send_file(self, path: str) -> None:
        """打印文件路径"""
        print(f"[文件: {path}]")

    def get_input(self, prompt: str = "") -> str:
        """获取输入"""
        try:
            return input(prompt)
        except EOFError:
            return ""

    def show_loading(self, message: str = "处理中..."):
        """显示加载"""
        print(f"⏳ {message}...")

        class LoadingCtx:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                print("✅ 完成")

        return LoadingCtx()

    def toast(self, message: str, duration: int = 3) -> None:
        """显示提示"""
        print(f"📢 {message}")

    def set_title(self, title: str) -> None:
        """设置标题（CLI下无效）"""
        pass

    def input(self, prompt: str = "") -> str:
        """获取输入"""
        try:
            return input(prompt)
        except (KeyboardInterrupt, EOFError):
            print("\n再见!")
            sys.exit(0)

    def call_llm(self, messages: list) -> str:
        """调用 LLM — 由外壳决定连接哪个 LLM"""
        llm_type = self.llm_config.get("type", "ollama")
        if llm_type == "ollama":
            return self._call_ollama(messages)
        elif llm_type in ("openai", "openai_compatible"):
            return self._call_openai(messages)
        else:
            return f"❌ 不支持的 LLM 类型: {llm_type}"

    def _call_ollama(self, messages: list) -> str:
        """调用 Ollama"""
        host = self.llm_config.get("host", "http://localhost:11434")
        model = self.llm_config.get("model", "qwen2.5:7b")
        url = f"{host}/api/chat"

        payload = {"model": model, "messages": messages, "stream": False}

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("message", {}).get("content", "")

    def _call_openai(self, messages: list) -> str:
        """调用 OpenAI 兼容 API"""
        host = self.llm_config.get("host", "http://localhost:11434")
        model = self.llm_config.get("model", "")
        api_key = self.llm_config.get("api_key", "")
        url = f"{host}/v1/chat/completions"

        payload = {"model": model, "messages": messages}

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )

        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
