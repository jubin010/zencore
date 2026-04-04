"""
Web外壳驱动 - 基于PyWebIO
通过 api_key 自动判断模型类别：
- api_key 为空或 "ollama" -> 使用 ollama 原生包
- 其他 -> 使用 openai SDK

支持思考模式（thinking）：自动剥离 <think> 标签，展示思考过程
"""

import re
from pywebio.output import put_text, put_html, put_image, put_file, toast
from pywebio.input import input, textarea
from core.agent import DriverInterface


class WebDriver(DriverInterface):
    """PyWebIO Web驱动"""

    def __init__(self, agent=None, llm_config=None):
        self.title = "zencore AI"
        self.agent = agent
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
        if self._client is None:
            if not self.api_key or self.api_key.lower() == "ollama":
                import ollama
                self._client = ollama.Client(host=self.host)
            else:
                from openai import OpenAI
                self._client = OpenAI(base_url=f"{self.host}/v1", api_key=self.api_key)
        return self._client

    def _extract_thinking(self, content: str) -> tuple:
        pattern = r'<think>(.*?)</think>\s*(.*)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        return "", content

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

            if self.thinking:
                thinking, answer = self._extract_thinking(content)
                if thinking:
                    put_html(f"<details><summary>💭 思考过程（点击展开）</summary><pre>{thinking}</pre></details>")
                return answer

            return content

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
