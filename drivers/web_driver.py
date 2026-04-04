"""
Web外壳驱动 - 基于PyWebIO
LLM 配置属于外壳，由驱动决定连接哪个 LLM
"""

import json
import urllib.request
import urllib.error
from pywebio.output import put_text, put_html, put_image, put_file, toast
from pywebio.input import input, textarea, input_group
from pywebio import config
from core.agent import DriverInterface


class WebDriver(DriverInterface):
    """PyWebIO Web驱动"""

    def __init__(self, agent=None, llm_config=None):
        self.title = "zencore AI"
        self.agent = agent
        self.llm_config = llm_config or {
            "type": "ollama",
            "host": "http://localhost:11434",
            "model": "qwen2.5:7b",
        }

    def send_message(self, content: str) -> None:
        """发送消息"""
        put_text(content)

    def send_html(self, html: str) -> None:
        """发送HTML"""
        put_html(html)

    def send_image(self, path: str) -> None:
        """发送图片"""
        put_image(path)

    def send_file(self, path: str, name: str = None) -> None:
        """发送文件"""
        with open(path, "rb") as f:
            data = f.read()
        put_file(name or path, data)

    def get_input(self, prompt: str = "") -> str:
        """获取输入"""
        return input(prompt)

    def get_textarea(self, prompt: str = "", **kwargs) -> str:
        """获取多行文本"""
        return textarea(prompt, **kwargs)

    def show_loading(self, message: str = "处理中..."):
        """显示加载"""
        return toast(message, duration=-1)

    def toast(self, message: str, duration: int = 3) -> None:
        """显示提示"""
        toast(message, duration=duration)

    def set_title(self, title: str) -> None:
        """设置标题"""
        self.title = title

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

    def run(self, host: str = "0.0.0.0", port: int = 8080):
        """运行 Web 服务"""
        from pywebio.platform.tornado import start_server
        from pywebio import session

        def main():
            put_html(f"<h1>{self.title}</h1>")
            while True:
                user_input = input("输入消息:")
                if not user_input:
                    continue
                put_text(f"👤 你: {user_input}")
                if self.agent:
                    response = self.agent.chat_with_tools(user_input)
                    put_text(f"🤖 AI: {response}")

        start_server(main, host=host, port=port, debug=False)
