"""
Web外壳驱动 - 基于PyWebIO
LLM 连接使用 openai SDK（兼容 Ollama 和 OpenAI）
"""

from pywebio.output import put_text, put_html, put_image, put_file, toast
from pywebio.input import input, textarea
from openai import OpenAI
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
        self.client = self._create_client()
        self.model = self.llm_config.get("model", "qwen2.5:7b")

    def _create_client(self) -> OpenAI:
        """创建 OpenAI 兼容客户端"""
        host = self.llm_config.get("host", "http://localhost:11434")
        api_key = self.llm_config.get("api_key", "ollama")

        return OpenAI(base_url=f"{host}/v1", api_key=api_key)

    def send_message(self, content: str) -> None:
        put_text(content)

    def send_html(self, html: str) -> None:
        put_html(html)

    def send_image(self, path: str) -> None:
        put_image(path)

    def send_file(self, path: str, name: str = None) -> None:
        with open(path, "rb") as f:
            data = f.read()
        put_file(name or path, data)

    def get_input(self, prompt: str = "") -> str:
        return input(prompt)

    def get_textarea(self, prompt: str = "", **kwargs) -> str:
        return textarea(prompt, **kwargs)

    def show_loading(self, message: str = "处理中..."):
        return toast(message, duration=-1)

    def toast(self, message: str, duration: int = 3) -> None:
        toast(message, duration=duration)

    def set_title(self, title: str) -> None:
        self.title = title

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

    def run(self, host: str = "0.0.0.0", port: int = 8080):
        """运行 Web 服务"""
        from pywebio.platform.tornado import start_server

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
