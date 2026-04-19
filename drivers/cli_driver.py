"""
CLI外壳驱动 - 命令行界面（Rich 美化版）
通过 api_key 自动判断模型类别：
- api_key 为空或 "ollama" -> 使用 ollama 原生包
- 其他 -> 使用 openai SDK

支持思考模式（thinking）：使用 response.message.thinking 字段
"""

import json
import re
import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.rule import Rule
from core.agent import DriverInterface

console = Console()


def _sanitize(text: str) -> str:
    """净化文本：移除 UTF-8 不支持的代理字符"""
    if not text:
        return ""
    # 移除 surrogate 字符
    text = re.sub(r"[\ud800-\udfff]", "", text)
    # 移除其他非法字符
    text = text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
    return text


def _parse_ollama_thinking_toolcalls(thinking: str) -> list:
    """从 Ollama thinking 文本中解析 tool_call 标签"""
    if not thinking:
        return []

    pattern = r"<tool_call>\s*<function=(\w+)([^>]*)>(?:<parameter=(\w+)>([^<]*)</parameter>)?([^<]*)</tool_call>"
    matches = re.findall(pattern, thinking)

    tool_calls = []
    for i, match in enumerate(matches):
        func_name = match[0]
        rest = match[1]
        param_name = match[2]
        param_value = match[3]

        arguments = {}
        if param_name and param_value:
            arguments[param_name] = param_value

        tool_calls.append(
            {
                "id": f"ollama_tc_thought_{i}_{id(thinking)}",
                "type": "function",
                "function": {
                    "name": func_name,
                    "arguments": json.dumps(arguments, ensure_ascii=False)
                    if arguments
                    else "{}",
                },
            }
        )

    return tool_calls


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
        self._silent = False

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

                self._client = ollama.Client(host=self.host, timeout=300)
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

    def send_message(self, content: str, force: bool = False) -> None:
        if force or not self._silent:
            console.print(Markdown(content))

    def send_image(self, path: str) -> None:
        if not self._silent:
            console.print(f"[bold yellow][图片: {path}][/]")

    def send_file(self, path: str) -> None:
        if not self._silent:
            console.print(f"[bold yellow][文件: {path}][/]")

    def get_input(self, prompt: str = "") -> str:
        try:
            # 使用原生 input 并保留图标，避开 Rich 的编码坑
            val = input("\n👤 你: ")
            return _sanitize(val)
        except EOFError:
            return ""

    def show_loading(self, message: str = "处理中..."):
        if not self._silent:
            console.print(f"[dim]⏳ {message}...[/]")

    def start_thinking(self):
        if self._silent:
            return
        from rich.spinner import Spinner
        from rich.live import Live

        spinner = Spinner("dots", text=f"[dim]{self.name} 正在思考...[/]")
        self._thinking_live = Live(spinner, console=console, transient=True)
        self._thinking_live.start()

    def stop_thinking(self):
        if self._silent:
            return
        if hasattr(self, "_thinking_live") and self._thinking_live:
            self._thinking_live.stop()
            self._thinking_live = None

    def toast(self, message: str, duration: int = 3) -> None:
        if not self._silent:
            console.print(Panel(message, title="📢 提示", border_style="yellow"))

    def set_title(self, title: str) -> None:
        pass

    def call_llm(self, messages: list, tools: list = None) -> dict:
        """调用 LLM — 根据 api_key 自动选择 SDK

        Returns:
            {
                "content": str,
                "tool_calls": list,  # 原生 tool_calls（OpenAI 格式）
                "thinking": str,
            }
        """
        try:
            client = self._get_client()

            if not self.api_key or self.api_key.lower() == "ollama":
                # Ollama SDK 要求 arguments 是 dict 而非 JSON 字符串
                ollama_messages = []
                for msg in messages:
                    if msg.get("role") == "assistant" and "tool_calls" in msg:
                        converted_tc = []
                        for tc in msg["tool_calls"]:
                            fn = tc.get("function", {})
                            args = fn.get("arguments", "{}")
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

                api_kwargs = {
                    "model": self.model,
                    "messages": ollama_messages,
                    "think": self.thinking,
                }
                if tools:
                    api_kwargs["tools"] = tools

                self.start_thinking()
                try:
                    response = client.chat(**api_kwargs)
                finally:
                    self.stop_thinking()

                thinking = (
                    _sanitize(response.message.thinking)
                    if hasattr(response.message, "thinking")
                    else ""
                )
                answer = _sanitize(response.message.content)

                # 转换 Ollama tool_calls 为 OpenAI 格式
                native_tool_calls = []
                if (
                    hasattr(response.message, "tool_calls")
                    and response.message.tool_calls
                ):
                    for tc in response.message.tool_calls:
                        native_tool_calls.append(
                            {
                                "id": getattr(tc, "id", f"ollama_tc_{id(tc)}"),
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": json.dumps(
                                        tc.function.arguments, ensure_ascii=False
                                    )
                                    if isinstance(tc.function.arguments, dict)
                                    else tc.function.arguments,
                                },
                            }
                        )

                # Ollama think 模式下 tool_calls 可能藏在 thinking 文本中
                if not native_tool_calls and self.thinking and thinking:
                    native_tool_calls = _parse_ollama_thinking_toolcalls(thinking)

                if self.thinking and thinking and not self._silent:
                    console.print(
                        Panel(
                            Markdown(thinking),
                            title=f"💭 {self.name} 思考过程",
                            border_style="blue",
                        )
                    )
                    console.print(Rule(style="dim"))

                return {
                    "content": answer,
                    "tool_calls": native_tool_calls,
                    "thinking": thinking,
                }

            elif self.api_key.lower() == "llama.cpp":
                extra_body = {"chat_template_kwargs": {}}
                if self.thinking:
                    extra_body["chat_template_kwargs"]["enable_thinking"] = True
                    extra_body["chat_template_kwargs"]["thinking_language"] = "zh"
                else:
                    extra_body["chat_template_kwargs"]["enable_thinking"] = False
                if self.thinking_mode and self.thinking_mode.startswith("extra_body:"):
                    key, val = self.thinking_mode[len("extra_body:") :].split("=", 1)
                    extra_body[key.strip()] = val.strip().lower() == "true"

                processed_messages = []
                for msg in messages:
                    if msg.get("role") == "assistant" and "tool_calls" in msg:
                        processed_tcs = []
                        for tc in msg["tool_calls"]:
                            fn = tc.get("function", {})
                            args = fn.get("arguments", "{}")
                            if isinstance(args, str):
                                try:
                                    args = json.loads(args)
                                except:
                                    args = {}
                            processed_tcs.append({
                                "id": tc.get("id", f"llama_tc_{id(tc)}"),
                                "type": "function",
                                "function": {
                                    "name": fn.get("name", ""),
                                    "arguments": args,
                                }
                            })
                        processed_messages.append({
                            "role": "assistant",
                            "content": msg.get("content") or "",
                            "tool_calls": processed_tcs,
                        })
                    else:
                        processed_messages.append(msg)

                api_kwargs = {
                    "model": self.model,
                    "messages": processed_messages,
                    "temperature": 0.7,
                }
                api_kwargs["extra_body"] = extra_body
                if tools:
                    api_kwargs["tools"] = tools

                self.start_thinking()
                try:
                    response = client.chat.completions.create(**api_kwargs)
                finally:
                    self.stop_thinking()

                message = response.choices[0].message

                thinking = ""
                if hasattr(message, "reasoning_details") and message.reasoning_details:
                    parts = []
                    for detail in message.reasoning_details:
                        if isinstance(detail, dict) and "text" in detail:
                            parts.append(detail["text"])
                        elif hasattr(detail, "text"):
                            parts.append(detail.text)
                    thinking = "\n".join(parts)
                elif hasattr(message, "thinking") and message.thinking:
                    thinking = _sanitize(message.thinking)
                elif hasattr(message, "model_extra") and message.model_extra:
                    rc = message.model_extra.get("reasoning_content", "")
                    if rc:
                        thinking = _sanitize(rc)

                if thinking and not self._silent:
                    console.print(
                        Panel(
                            Markdown(thinking),
                            title=f"💭 {self.name} 思考过程",
                            border_style="blue",
                        )
                    )
                    console.print(Rule(style="dim"))

                native_tool_calls = []
                if hasattr(message, "tool_calls") and message.tool_calls:
                    for tc in message.tool_calls:
                        native_tool_calls.append(
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                        )

                return {
                    "content": _sanitize(message.content) if message.content else "",
                    "tool_calls": native_tool_calls,
                    "thinking": thinking,
                }

            else:
                extra_body = {}
                if self.thinking_mode == "reasoning_split":
                    extra_body["reasoning_split"] = True
                elif self.thinking_mode and self.thinking_mode.startswith(
                    "extra_body:"
                ):
                    key, val = self.thinking_mode[len("extra_body:") :].split("=", 1)
                    extra_body[key.strip()] = val.strip().lower() == "true"

                api_kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                }
                if extra_body:
                    api_kwargs["extra_body"] = extra_body
                if tools:
                    api_kwargs["tools"] = tools

                self.start_thinking()
                try:
                    response = client.chat.completions.create(**api_kwargs)
                finally:
                    self.stop_thinking()

                message = response.choices[0].message

                thinking = ""
                if self.thinking_mode == "reasoning_split":
                    thinking = _sanitize(self._extract_thinking_from_openai(message))
                elif hasattr(message, "thinking") and message.thinking:
                    thinking = _sanitize(message.thinking)

                if thinking and not self._silent:
                    console.print(
                        Panel(
                            Markdown(thinking),
                            title=f"💭 {self.name} 思考过程",
                            border_style="blue",
                        )
                    )
                    console.print(Rule(style="dim"))

                # 提取原生 tool_calls
                native_tool_calls = []
                if hasattr(message, "tool_calls") and message.tool_calls:
                    for tc in message.tool_calls:
                        native_tool_calls.append(
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                        )

                return {
                    "content": _sanitize(message.content),
                    "tool_calls": native_tool_calls,
                    "thinking": thinking,
                }

        except Exception as e:
            return {
                "content": f"❌ LLM调用失败: {str(e)}",
                "tool_calls": [],
                "thinking": "",
            }
