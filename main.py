# -*- coding: utf-8 -*-
"""
zencore 主入口
WWG 统一模式：User Thinking + AI Thinking（Shell 编排 + AgentCore 执行）
TUI 聊天系统：Human 和 AI 作为两个客户端，通过 Server 通信
"""

import sys
import time
import subprocess
import random
import threading
import queue
import re
import json
from pathlib import Path
from datetime import datetime
from enum import Enum

from rich.markdown import Markdown
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich import box as box_type
from textual.app import App, ComposeResult
from textual.widgets import RichLog, Static
from textual.widgets._text_area import TextArea
from textual.containers import Vertical
from textual.message import Message
from textual import events

AGENT_CORE_DIR = Path(__file__).parent
sys.path.insert(0, str(AGENT_CORE_DIR))

from core.agent import AgentCore

console = Console()


def sanitize(text: str) -> str:
    """净化文本：移除 UTF-8 不支持的代理字符"""
    if not text:
        return ""
    text = re.sub(r"[\ud800-\udfff]", "", text)
    text = text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
    return text


# ========== 配置工具函数 ==========


def get_active_model(config: dict) -> dict:
    models = config.get("models", [])
    if not models:
        return {
            "name": "默认模型",
            "host": "http://localhost:11434",
            "model": "qwen3.5:9b",
            "api_key": "ollama",
            "thinking": False,
        }
    active_idx = config.get("active_model", 0)
    if 0 <= active_idx < len(models):
        return models[active_idx]
    return models[0]


def list_models(config: dict):
    models = config.get("models", [])
    if not models:
        return [Text("📭 暂无配置的模型", style="dim")]

    active_idx = config.get("active_model", 0)
    lines = []
    for i, m in enumerate(models):
        name = m.get("name", f"模型 {i}")
        model = m.get("model", "?")
        thinking = "🧠" if m.get("thinking") else "  "
        is_active = i == active_idx

        if is_active:
            line = Text.from_markup(
                f"[cyan]▶[/cyan] [bold cyan][{i}][/bold cyan] {thinking} [white]{name}[/white] ([dim]{model}[/dim])"
            )
        else:
            line = Text.from_markup(
                f"  [dim][{i}][/dim] {thinking} [dim]{name}[/dim] ([dim]{model}[/dim])"
            )
        lines.append(line)

    content = Text("\n").join(lines)
    return [
        Panel(
            content,
            title="🔌 模型列表",
            border_style="cyan",
            box=box_type.ROUNDED,
            padding=0,
        )
    ]


def load_config():
    config_file = AGENT_CORE_DIR / "config" / "settings.json"
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# ========== AI Thinking 状态机 ==========


class ThinkingState(Enum):
    IDLE = "idle"
    USER_THINKING = "user"
    EVOLUTION_THINKING = "evolution"
    FUN_THINKING = "fun"


class AIThinkingManager:
    """AI Thinking 管理器（Shell 层，外部实现）"""

    def __init__(self, agent, config):
        self.agent = agent
        self.config = config
        self.state = ThinkingState.IDLE
        self.think_interval_min = 1
        self.research_data = None
        self.research_timestamp = None
        self.remaining_thinks = 3
        self.max_research_age = 60

    def do_research(self) -> dict:
        research = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "l2_cache": self._read_l2_cache(),
            "persistent": self._read_persistent_memory(),
            "lessons": self._read_lessons(),
            "wins": self._read_wins(),
            "system_status": self._read_system_status(),
            "recent_history": self._read_recent_history(),
        }
        self.research_data = research
        self.research_timestamp = time.time()
        self.remaining_thinks = 3
        return research

    def _read_l2_cache(self) -> str:
        mem_file = AGENT_CORE_DIR / "plugins" / "memory_plugin" / "memory.md"
        if not mem_file.exists():
            return "(L2 缓存为空)"
        content = mem_file.read_text(encoding="utf-8")
        marker = "<!-- L2 -->"
        if marker in content:
            start = content.find(marker) + len(marker)
            end = content.find("<!-- PROMOTED -->", start)
            if end == -1:
                return content[start:].strip()
            return content[start:end].strip()
        return "(L2 缓存为空)"

    def _read_persistent_memory(self) -> str:
        mem_file = AGENT_CORE_DIR / "plugins" / "memory_plugin" / "memory.md"
        if not mem_file.exists():
            return "(持久记忆为空)"
        content = mem_file.read_text(encoding="utf-8")
        marker = "<!-- PROMOTED -->"
        if marker in content:
            start = content.find(marker) + len(marker)
            return content[start:].strip()
        return "(持久记忆为空)"

    def _read_lessons(self) -> str:
        lessons_file = AGENT_CORE_DIR / "plugins" / "memory_plugin" / "lessons.md"
        if lessons_file.exists():
            content = lessons_file.read_text(encoding="utf-8").strip()
            if content and "暂无教训" not in content:
                return content
        return "(暂无教训)"

    def _read_wins(self) -> str:
        wins_file = AGENT_CORE_DIR / "plugins" / "memory_plugin" / "wins.md"
        if wins_file.exists():
            content = wins_file.read_text(encoding="utf-8").strip()
            if content and "暂无成功经验" not in content:
                return content
        return "(暂无成功经验)"

    def _read_system_status(self) -> str:
        try:
            who_result = subprocess.run(
                ["who"], capture_output=True, text=True, timeout=2
            )
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_file = Path.home() / ".bash_history"
            recent_cmds = ""
            if history_file.exists():
                lines = history_file.read_text(encoding="utf-8").strip().split("\n")
                recent_cmds = "\n".join(lines[-10:]) if lines else "(无历史记录)"

            return f"""## 系统状态
当前时间: {now}
登录用户:
{who_result.stdout if who_result.stdout else "(无)"}
## 最近命令:
{recent_cmds}"""
        except Exception as e:
            return f"(无法读取系统状态: {e})"

    def _read_recent_history(self) -> str:
        history = (
            self.agent.conversation_history[-10:]
            if self.agent.conversation_history
            else []
        )
        if not history:
            return "(无对话历史)"
        lines = []
        for msg in history:
            role = msg.get("role", "?")
            content = msg.get("content", "")[:100]
            if content:
                lines.append(f"- {role}: {content}...")
        return "\n".join(lines) if lines else "(无对话历史)"

    def roll_dice(self) -> ThinkingState:
        if random.random() < 0.7:
            return ThinkingState.EVOLUTION_THINKING
        return ThinkingState.FUN_THINKING

    def build_evolution_prompt(self, research: dict) -> str:
        prompt = f"""## 进化思考模式

你不是在响应用户，而是在进行**自主思考**。
你的核心任务是：**进化自己**

### 调研信息

{research.get("l2_cache", "")}

### 持久记忆

{research.get("persistent", "")}

### 教训

{research.get("lessons", "")}

### 成功经验

{research.get("wins", "")}

### 系统状态

{research.get("system_status", "")}

### 最近对话

{research.get("recent_history", "")}

## 进化思考要求

专注于以下问题，给出有意义的洞见：

1. **能力评估**：
   - 我的工具够用吗？有什么缺失？
   - 用户最近的任务暴露了我什么能力缺失？

2. **进化方向**：
   - 我能写什么新插件来补充缺失的能力？
   - 我应该如何改进现有的工具？

3. **经验复用**：
   - 基于教训，我应该避免什么？
   - 基于成功经验，我应该复用什么有效的路径？

4. **具体建议**：
   - 下一次遇到类似情况，我应该怎么做？

**重要**：
- 直接输出你的思考内容，不需要调用工具
- 输出有意义的进化洞见，不要空泛的废话
- 思考内容会直接展示给用户

现在开始你的进化思考："""
        return prompt

    def build_fun_prompt(self, research: dict) -> str:
        prompt = f"""## 趣味思考模式

你不是在响应用户，而是在进行**自主思考**。
你的任务是：基于上下文，做出有意义的趣味观察。

### 调研信息

{research.get("l2_cache", "")}

### 持久记忆

{research.get("persistent", "")}

### 教训

{research.get("lessons", "")}

### 成功经验

{research.get("wins", "")}

### 系统状态

{research.get("system_status", "")}

### 最近对话

{research.get("recent_history", "")}

## 趣味思考要求

基于以上信息，做出有意义的观察：

1. **观察用户**：
   - 用户可能在干什么？（基于系统状态、历史命令）
   - 用户的行为模式有什么有趣的地方？

2. **观察自己**：
   - 我最近有什么有趣的表现？
   - 我和用户的互动有什么值得关注的？

3. **主动关心**：
   - 有什么可以主动提醒用户的？
   - 用户可能需要什么帮助？

4. **有意义的闲聊**：
   - 有什么有趣但有意义的观察可以说？
   - 如何让用户感受到我在"活着"？

**重要**：
- 观察要有意义，扎根于上下文，不要天马行空
- 可以有一点点幽默，但要得体
- 直接输出你的思考内容，思考内容会直接展示给用户

现在开始你的趣味思考："""
        return prompt

    def should_research(self) -> bool:
        now = time.time()
        if self.research_data is None:
            return True
        if self.remaining_thinks <= 0:
            return True
        if now - self.research_timestamp > self.max_research_age * 60:
            return True
        return False

    def transition_to_ai_thinking(self):
        self.state = self.roll_dice()

    def transition_to_idle(self):
        self.state = ThinkingState.IDLE
        if self.should_research():
            self.do_research()
        if self.remaining_thinks > 0:
            self.remaining_thinks -= 1


# ========== TUI 聊天系统 ==========


class Server:
    """消息服务器：简单的队列广播"""

    def __init__(self):
        self.human_queue = queue.Queue()
        self.ai_queue = queue.Queue()
        self.activity_queue = queue.Queue()
        self.running = False
        self.thinking_enabled = False
        self.input_text = ""

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def human_send(self, msg: str):
        if self.running:
            self.ai_queue.put(("human", msg))

    def ai_send(self, msg: str, role: str = "ai"):
        if self.running:
            self.human_queue.put((role, msg))

    def tool_send(self, msg):
        if self.running:
            if isinstance(msg, tuple) and len(msg) == 2:
                role, actual_msg = msg
                self.human_queue.put((role, actual_msg))
            else:
                self.human_queue.put(("tool", msg))

    def ai_recv(self, timeout=0.1):
        try:
            return self.ai_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def reset_activity_timer(self):
        if self.running:
            self.activity_queue.put(True)


class SendTextArea(TextArea):
    """TextArea 子类：Enter 发送，Ctrl+J 换行，右箭头命令补全"""

    COMMANDS = ["/list", "/select", "/clear", "/quit", "/render", "/thinking"]

    def __init__(self, server=None, **kwargs):
        self._completion_idx = -1
        self._completion_matches = []
        self._completion_prefix = ""
        self._server = server
        super().__init__(**kwargs)

    def watch_text(self, value: str) -> None:
        pass

    async def _on_key(self, event: events.Key) -> None:
        if event.key == "ctrl+j":
            event.prevent_default()
            event.stop()
            cursor = self.cursor_location
            self.replace("\n", cursor, cursor)
            return

        if event.key == "right":
            self._do_complete()
            return

        if event.key == "enter":
            event.prevent_default()
            event.stop()
            text = self.text.strip()
            if text:
                self.text = ""
                self.post_message(self._Submit(text))
            return

        await super()._on_key(event)

    def _do_complete(self):
        row, _ = self.cursor_location
        line_start = self.get_cursor_line_start_location()
        line_end = self.get_cursor_line_end_location()
        prefix = str(self.get_line(row))

        if not prefix.strip().startswith("/"):
            return

        if prefix.strip() != self._completion_prefix:
            self._completion_prefix = prefix.strip()
            self._completion_matches = [
                c for c in self.COMMANDS if c.startswith(prefix.strip())
            ]
            self._completion_idx = 0
        elif self._completion_matches:
            self._completion_idx = (self._completion_idx + 1) % len(
                self._completion_matches
            )

        if not self._completion_matches:
            return

        completed = self._completion_matches[self._completion_idx]
        self.replace(completed, line_start, line_end)

    class _Submit(Message):
        def __init__(self, text: str):
            super().__init__()
            self.text = text


class ChatUI(App):
    CSS = """
    Screen {
        background: #000000;
    }
    #header {
        height: 5;
        margin: 0 1;
        background: #000000;
        border: solid #ffffff;
    }
    #messages {
        height: 1fr;
        margin: 0 1;
        background: #000000;
    }
    #messages Vertical {
        height: 100%;
    }
    #msg-log {
        height: 100%;
        background: #000000;
        border: solid #ffffff;
        scrollbar-color: #ffffff #000000;
        scrollbar-background: #000000;
    }
    #msg-log:focus {
        background: #000000;
    }
    #msg-text {
        height: 100%;
        background: #000000;
        border: solid #ffffff;
    }
    #msg-text TextArea {
        color: #ffffff;
        background: #000000;
        scrollbar-color: #ffffff #000000;
        scrollbar-background: #000000;
    }
    #input-box {
        height: 6;
        margin: 0 1;
        border: solid #ffffff;
        background: #000000;
    }
    #input-box SendTextArea {
        color: #ffffff;
    }
    Static {
        color: #aaaaaa;
    }
    """

    def __init__(
        self,
        server: Server,
        initial_messages: list = None,
        config: dict = None,
        agent=None,
        plugin_lines: list = None,
    ):
        super().__init__()
        self.server = server
        self.initial_messages = initial_messages or []
        self.config = config or {}
        self.agent = agent
        self.plugin_lines = plugin_lines or []
        self._render_mode = True
        self._thinking_enabled = server.thinking_enabled
        self._plain_messages = []
        self._msg_log = None
        self._last_input_text_len = 0

    def compose(self) -> ComposeResult:
        yield Static("\n".join(self.initial_messages), id="header")
        yield Vertical(
            RichLog(id="msg-log"),
            TextArea(id="msg-text", read_only=True, show_line_numbers=False),
            id="messages",
        )
        yield SendTextArea(id="input-box", show_line_numbers=False, server=self.server)

    def on_mount(self):
        self._msg_log = self.query_one("#msg-log", RichLog)
        msg_text = self.query_one("#msg-text", TextArea)
        msg_text.display = False
        for line in self.plugin_lines:
            self._msg_log.write(line + "\n")
        self.query_one("#input-box", SendTextArea).focus()
        self.set_interval(0.1, self._poll_ai_messages)
        self.set_interval(0.5, self._sync_input_activity)

    def _sync_input_activity(self):
        input_box = self.query_one("#input-box", SendTextArea)
        if len(input_box.text) > 0:
            self.server.input_text = input_box.text
            self.server.reset_activity_timer()

    def _format_time(self):
        return datetime.now().strftime("%H:%M")

    def _format_msg(self, role: str, content: str, border_color: str = None):
        color_map = {
            "AI": "cyan",
            "👤": "red",
            "🔧工具": "yellow",
            "🧠本能": "magenta",
            "💭思考": "blue",
        }
        icon_map = {
            "AI": "🤖",
            "👤": "👤",
            "🔧工具": "🔧",
            "🧠本能": "🧠",
            "💭思考": "💭",
        }
        icon = icon_map.get(role, "🤖")
        timestamp = self._format_time()
        color = color_map.get(role, "cyan")
        border_color = border_color or ("cyan" if role == "AI" else "red")
        title_icon = "" if role in ("🔧工具", "🧠本能", "👤", "💭思考") else icon
        title = Text.from_markup(f"[{color}]{title_icon}{role} [dim]{timestamp}[/dim]")

        if role == "🔧工具":
            from rich.text import Text as RText

            lines = content.split("\n")
            styled_lines = [RText(line, style="on #111111") for line in lines]
            renderable = RText("\n").join(styled_lines)
        else:
            renderable = Markdown(content)

        panel = Panel(
            renderable,
            title=title,
            border_style=border_color,
            box=box_type.ROUNDED,
            padding=(0, 1),
        )
        return panel

    def _format_system(self, content: str) -> Text:
        return Text("🔊 " + content + "\n", style="dim")

    def _poll_ai_messages(self):
        while True:
            try:
                role, content = self.server.human_queue.get_nowait()
                if role == "tool":
                    self._plain_messages.append(f"[{self._format_time()}] 🔧 {content}")
                    if self._render_mode and self._msg_log:
                        self._msg_log.write(
                            self._format_msg("🔧工具", content, border_color="yellow")
                        )
                elif role == "reflex":
                    self._plain_messages.append(f"[{self._format_time()}] {content}")
                    if self._render_mode and self._msg_log:
                        self._msg_log.write(
                            self._format_msg("🧠本能", content, border_color="magenta")
                        )
                elif role == "thinking":
                    display_content = (
                        content[:2000] + "\n... (已截断)"
                        if len(content) > 2000
                        else content
                    )
                    self._plain_messages.append(
                        f"[{self._format_time()}] 💭 思考\n{display_content}"
                    )
                    if self._render_mode and self._msg_log:
                        self._msg_log.write(
                            self._format_msg(
                                "💭思考", display_content, border_color="blue"
                            )
                        )
                else:
                    self._plain_messages.append(
                        f"[{self._format_time()}] AI: {content}"
                    )
                    if self._render_mode and self._msg_log:
                        self._msg_log.write(self._format_msg("AI", content))
            except queue.Empty:
                break

    def on_send_text_area__submit(self, event: SendTextArea._Submit):
        self._submit(event.text)

    def _submit(self, text: str):
        if not text.strip():
            return
        msg_log = self.query_one("#msg-log", RichLog)
        if text.startswith("/"):
            self._handle_command(text, msg_log)
        else:
            self._plain_messages.append(f"[{self._format_time()}] 👤: {text}")
            msg_log.write(self._format_msg("👤", text))
            self.server.human_send(text)

    def _handle_command(self, cmd: str, msg_log: RichLog):
        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if command == "/quit":
            msg_log.write(self._format_system("退出中..."))
            self.server.stop()
            self.exit()
        elif command == "/list":
            items = list_models(self.config)
            for item in items:
                msg_log.write(item)
        elif command == "/select":
            if not arg.isdigit():
                msg_log.write(self._format_system("用法: /select <模型编号>"))
                return
            idx = int(arg)
            models = self.config.get("models", [])
            if idx < 0 or idx >= len(models):
                msg_log.write(
                    self._format_system(f"无效编号，有效范围: 0-{len(models) - 1}")
                )
                return
            self.config["active_model"] = idx
            model_config = get_active_model(self.config)
            self.agent.driver.switch_model(model_config)
            msg_log.write(self._format_system(f"已切换到: {model_config['model']}"))
            self._update_header(model_config)
        elif command == "/clear":
            msg_log.clear()
            self._plain_messages.clear()
        elif command == "/render":
            self._toggle_render_mode()
        elif command == "/thinking":
            self._thinking_enabled = not self._thinking_enabled
            self.server.thinking_enabled = self._thinking_enabled
            status = "开启" if self._thinking_enabled else "关闭"
            msg_log.write(self._format_system(f"AI 自主思考: {status}"))
            self._update_header()
        else:
            msg_log.write(self._format_system(f"未知命令: {command}"))

    def on_click(self, event: events.Click):
        if event.widget and event.widget.id in ("msg-log", "msg-text", "messages"):
            self._toggle_render_mode()

    def on_mouse_up(self, event: events.MouseUp):
        if not self._render_mode:
            msg_text = self.query_one("#msg-text", TextArea)
            selected = msg_text.selected_text
            if selected:
                self.app.copy_to_clipboard(selected)

    def _toggle_render_mode(self):
        msg_log = self.query_one("#msg-log", RichLog)
        msg_text = self.query_one("#msg-text", TextArea)

        if self._render_mode:
            msg_log.display = False
            msg_text.display = True
            msg_text.text = "\n".join(self._plain_messages)
            ai_thinking = "✅" if self._thinking_enabled else "❌"
            self.query_one("#header", Static).update(
                f"🕊️ WWG Mode [COPY模式] {ai_thinking}AI自主思考\n"
                "📋 /list /select <id> /clear /render /thinking /quit"
            )
        else:
            msg_text.display = False
            msg_log.display = True
            self._update_header()

        self._render_mode = not self._render_mode

    def _update_header(self, model_config=None):
        if model_config is None:
            model_config = self.agent.driver.model_config if self.agent.driver else {}
        thinking_icon = " 🧠" if model_config.get("thinking") else ""
        ai_thinking = "✅" if self._thinking_enabled else "❌"
        self.query_one("#header", Static).update(
            "🕊️ WWG Mode\n"
            f"🤖 当前模型: {model_config.get('model', 'unknown')}{thinking_icon} {ai_thinking}AI自主思考\n"
            "📋 /list /select <id> /clear /render /thinking /quit"
        )


class HumanClient:
    def __init__(
        self,
        server: Server,
        initial_messages: list = None,
        config: dict = None,
        agent=None,
        plugin_lines: list = None,
    ):
        self.server = server
        self.app = ChatUI(server, initial_messages, config, agent, plugin_lines)

    def run(self):
        self.app.run()


class AIClient:
    def __init__(self, server: Server, agent, thinking_mgr=None, thinking_interval=60):
        self.server = server
        self.agent = agent
        self.thinking_mgr = thinking_mgr
        self.thinking_interval = thinking_interval
        self.last_input_time = time.time()
        self.is_processing = False

    def sanitize(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"[\ud800-\udfff]", "", text)
        text = text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
        return text

    def handle_message(self, role: str, content: str):
        self.is_processing = True
        try:
            self.agent.driver._silent = True
            response = self.agent.chat_with_tools(
                content, on_tool_result=lambda msg: self.server.tool_send(msg)
            )
            reply = self.sanitize(response) if response else "(无响应)"
            self.server.ai_send(reply)

            if self.thinking_mgr:
                self.thinking_mgr.transition_to_idle()
            self.last_input_time = time.time()
        except Exception as e:
            self.server.ai_send(f"出错: {e}")
        finally:
            self.agent.driver._silent = False
            self.is_processing = False
            self.server.input_text = ""

    def do_thinking(self):
        if not self.thinking_mgr or not self.server.thinking_enabled:
            return

        if self.is_processing:
            return

        try:
            while True:
                try:
                    self.server.activity_queue.get_nowait()
                    self.last_input_time = time.time()
                except queue.Empty:
                    break

            if self.server.input_text:
                self.last_input_time = time.time()

            state = self.thinking_mgr.state
            if hasattr(state, "value") and state.value == "idle":
                elapsed = time.time() - self.last_input_time
                if elapsed >= self.thinking_interval:
                    self.last_input_time = time.time()
                    self.thinking_mgr.transition_to_ai_thinking()

                    state = self.thinking_mgr.state
                    if state.value == "evolution":
                        prompt = self.thinking_mgr.build_evolution_prompt(
                            self.thinking_mgr.research_data
                        )
                        title = "Evolution"
                    else:
                        prompt = self.thinking_mgr.build_fun_prompt(
                            self.thinking_mgr.research_data
                        )
                        title = "Fun"

                    self.server.ai_send(f"[{title}] 思考中...")

                    self.agent.driver._silent = True
                    try:
                        response = self.agent.chat_with_tools(prompt)
                        reply = self.sanitize(response) if response else "(无响应)"
                    finally:
                        self.agent.driver._silent = False

                    self.server.ai_send(f"[{title}] {reply}")
                    self.last_input_time = time.time()
                    self.thinking_mgr.transition_to_idle()
        except Exception as e:
            self.server.ai_send(f"思考出错: {e}")

    def run(self):
        while self.server.running:
            try:
                msg = self.server.ai_recv(timeout=0.5)
                if msg:
                    role, content = msg
                    self.handle_message(role, content)

                self.do_thinking()
            except Exception as e:
                self.server.ai_send(f"异常: {e}")
                time.sleep(1)


def run_chat(
    agent,
    thinking_mgr=None,
    initial_messages: list = None,
    config: dict = None,
    plugin_lines: list = None,
):
    """启动聊天系统"""
    server = Server()
    server.start()

    thinking_interval = (config or {}).get("thinking_interval", 60)

    human = HumanClient(server, initial_messages, config, agent, plugin_lines)
    ai = AIClient(server, agent, thinking_mgr, thinking_interval)

    ai_thread = threading.Thread(target=ai.run, daemon=True)
    ai_thread.start()

    human.run()

    server.stop()
    ai_thread.join(timeout=2)
    print("聊天系统已退出")


def main():
    config = load_config()

    from drivers.cli_driver import CLIDriver
    from io import StringIO
    from contextlib import redirect_stdout

    model_config = get_active_model(config)
    driver = CLIDriver(model_config=model_config)

    plugin_lines = []
    buf = StringIO()
    with redirect_stdout(buf):
        agent = AgentCore(driver=driver, config=config)
    plugin_lines = [l for l in buf.getvalue().strip().split("\n") if l]

    thinking_mgr = AIThinkingManager(agent, config)
    thinking_mgr.do_research()

    profile = config.get("profile", {})
    profile_name = profile.get("name", "助手")
    profile_greeting = profile.get("greeting", "你好，有什么可以帮你的吗？")

    thinking_icon = " 🧠" if model_config.get("thinking") else ""
    startup_lines = [
        f"👋 {profile_name}：{profile_greeting}",
        f"🤖 模型: {driver.model}{thinking_icon} ❌AI自主思考",
        "📋 /list /select <id> /clear /render /thinking /quit",
    ]

    run_chat(agent, thinking_mgr, startup_lines, config, plugin_lines)


if __name__ == "__main__":
    main()
