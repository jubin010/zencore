"""
CLI外壳驱动 - 命令行界面（Rich 美化版）
通过 api_key 自动判断模型类别：
- api_key 为空或 "ollama" -> 使用 ollama 原生包
- 其他 -> 使用 openai SDK

支持思考模式（thinking）：使用 response.message.thinking 字段
"""

import re
import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.rule import Rule
from core.agent import DriverInterface

console = Console()


def _sanitize(text: str) -> str:
    """净化文本：移除 UTF-8 不支持的代理字符 (Surrogates U+D800-U+DFFF)"""
    return re.sub(r"[\ud800-\udfff]", "", text) if text else ""


class CLIDriver(DriverInterface):
    """命令行驱动（Rich 美化版）"""

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
        if hasattr(message, "reasoning_details") and message.reasoning_details:
            parts = []
            for detail in message.reasoning_details:
                if isinstance(detail, dict) and "text" in detail:
                    parts.append(detail["text"])
                elif hasattr(detail, "text"):
                    parts.append(detail.text)
            return "\n".join(parts)
        return ""

    def send_message(self, content: str) -> None:
        console.print(Markdown(content))

    def send_image(self, path: str) -> None:
        console.print(f"[bold yellow][图片: {path}][/]")

    def send_file(self, path: str) -> None:
        console.print(f"[bold yellow][文件: {path}][/]")

    def get_input(self, prompt: str = "") -> str:
        try:
            # 使用原生 input 并保留图标，避开 Rich 的编码坑
            val = input("\n👤 你: ")
            return _sanitize(val)
        except EOFError:
            return ""

    def show_loading(self, message: str = "处理中..."):
        console.print(f"[dim]⏳ {message}...[/]")

    def toast(self, message: str, duration: int = 3) -> None:
        console.print(Panel(message, title="📢 提示", border_style="yellow"))

    def set_title(self, title: str) -> None:
        pass

    def call_llm(self, messages: list) -> str:
        """调用 LLM — 根据 api_key 自动选择 SDK"""
        try:
            client = self._get_client()

            if not self.api_key or self.api_key.lower() == "ollama":
                # Ollama SDK 要求 arguments 是 dict 而非 JSON 字符串
                # 需要将 OpenAI 格式转换为 Ollama 格式
                ollama_messages = []
                for msg in messages:
                    if msg.get("role") == "assistant" and "tool_calls" in msg:
                        converted_tc = []
                        for tc in msg["tool_calls"]:
                            fn = tc.get("function", {})
                            args = fn.get("arguments", "{}")
                            # 字符串 → dict
                            if isinstance(args, str):
                                try:
                                    args = json.loads(args)
                                except:
                                    args = {}
                            converted_tc.append(
                                {
                                    "function": {
                                        "name": fn.get("name", ""),
                                        "arguments": args,
                                    }
                                }
                            )
                        ollama_messages.append(
                            {
                                "role": "assistant",
                                "content": msg.get("content") or "",
                                "tool_calls": converted_tc,
                            }
                        )
                    elif msg.get("role") == "tool":
                        ollama_messages.append(
                            {
                                "role": "tool",
                                "content": msg.get("content", ""),
                                "tool_call_id": msg.get("tool_call_id", ""),
                            }
                        )
                    else:
                        ollama_messages.append(msg)

                response = client.chat(
                    model=self.model,
                    messages=ollama_messages,
                    think=self.thinking,
                )

                thinking = (
                    _sanitize(response.message.thinking)
                    if hasattr(response.message, "thinking")
                    else ""
                )
                answer = _sanitize(response.message.content)

                if self.thinking and thinking:
                    console.print(
                        Panel(
                            Markdown(thinking), title="💭 思考过程", border_style="blue"
                        )
                    )
                    console.print(Rule(style="dim"))
                    return answer

                return answer

            else:
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

                if self.thinking and self.thinking_mode == "reasoning_split":
                    thinking = _sanitize(self._extract_thinking_from_openai(message))
                    if thinking:
                        console.print(
                            Panel(
                                Markdown(thinking),
                                title="💭 思考过程",
                                border_style="blue",
                            )
                        )
                        console.print(Rule(style="dim"))
                    return _sanitize(message.content)

                if self.thinking and hasattr(message, "thinking") and message.thinking:
                    thinking = _sanitize(message.thinking)
                    console.print(
                        Panel(
                            Markdown(thinking), title="💭 思考过程", border_style="blue"
                        )
                    )
                    console.print(Rule(style="dim"))
                    return _sanitize(message.content)

                return _sanitize(message.content)

        except Exception as e:
            return f"❌ LLM调用失败: {str(e)}"
