# -*- coding: utf-8 -*-
"""
zencore 主入口
WWG 统一模式：User Thinking + AI Thinking（Shell 编排 + AgentCore 执行）
"""

import sys
import time
import select
import subprocess
import random
import os
from pathlib import Path
from datetime import datetime
from enum import Enum

AGENT_CORE_DIR = Path(__file__).parent
sys.path.insert(0, str(AGENT_CORE_DIR))

import readline
from core.agent import AgentCore
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


# ========== AI Thinking 状态机 ==========


class ThinkingState(Enum):
    IDLE = "idle"  # 等待
    USER_THINKING = "user"  # 响应用户（不可打断）
    EVOLUTION_THINKING = "evolution"  # 进化思考（70%）
    FUN_THINKING = "fun"  # 趣味思考（30%）


class AIThinkingManager:
    """AI Thinking 管理器（Shell 层，外部实现）"""

    def __init__(self, agent, config):
        self.agent = agent
        self.config = config

        # 状态
        self.state = ThinkingState.IDLE

        # 思考控制
        self.next_think_time = None  # 下次 AI Thinking 的触发时间
        self.think_interval_min = 1  # 保底 1 分钟（测试用）

        # 调研控制
        self.research_data = None
        self.research_timestamp = None
        self.remaining_thinks = 3
        self.max_research_age = 60  # 调研结果最多撑 60 分钟

        # 用户输入缓冲

    # ========== 调研机制 ==========

    def do_research(self) -> dict:
        """执行调研，收集思考所需的信息"""
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
        """读取 L2 缓存区"""
        mem_file = AGENT_CORE_DIR / "plugins" / "memory_plugin" / "memory.md"
        if not mem_file.exists():
            return "(L2 缓存为空)"
        content = mem_file.read_text(encoding="utf-8")
        # 提取 L2 缓存区内容
        marker = "<!-- L2 -->"
        if marker in content:
            start = content.find(marker) + len(marker)
            end = content.find("<!-- PROMOTED -->", start)
            if end == -1:
                return content[start:].strip()
            return content[start:end].strip()
        return "(L2 缓存为空)"

    def _read_persistent_memory(self) -> str:
        """读取持久记忆区"""
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
        """读取教训"""
        lessons_file = AGENT_CORE_DIR / "plugins" / "memory_plugin" / "lessons.md"
        if lessons_file.exists():
            content = lessons_file.read_text(encoding="utf-8").strip()
            if content and "暂无教训" not in content:
                return content
        return "(暂无教训)"

    def _read_wins(self) -> str:
        """读取成功经验"""
        wins_file = AGENT_CORE_DIR / "plugins" / "memory_plugin" / "wins.md"
        if wins_file.exists():
            content = wins_file.read_text(encoding="utf-8").strip()
            if content and "暂无成功经验" not in content:
                return content
        return "(暂无成功经验)"

    def _read_system_status(self) -> str:
        """读取系统状态"""
        try:
            # 用户登录信息
            who_result = subprocess.run(
                ["who"], capture_output=True, text=True, timeout=2
            )
            # 当前时间
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # bash history 最近命令
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
        """读取最近的对话历史"""
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

    # ========== 思考 Prompt 构建 ==========

    def roll_dice(self) -> ThinkingState:
        """投掷骰子，决定思考类型"""
        if random.random() < 0.7:
            return ThinkingState.EVOLUTION_THINKING
        return ThinkingState.FUN_THINKING

    def build_evolution_prompt(self, research: dict) -> str:
        """构建进化思考的 Prompt"""
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
        """构建趣味思考的 Prompt"""
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

    # ========== 思考触发判断 ==========

    def should_research(self) -> bool:
        """判断是否需要重新调研"""
        now = time.time()

        # 首次必须调研
        if self.research_data is None:
            return True

        # 思考次数用尽
        if self.remaining_thinks <= 0:
            return True

        # 调研过期
        if now - self.research_timestamp > self.max_research_age * 60:
            return True

        return False

    def should_think(self) -> bool:
        """判断是否该触发 AI Thinking"""
        if self.state != ThinkingState.IDLE:
            return False

        # 检查是否到了思考时间
        if self.next_think_time is None:
            return True  # 第一次思考

        return time.time() >= self.next_think_time

    def calculate_next_think_time(self) -> int:
        """AI 自主决定下次思考间隔（分钟）"""
        return self.think_interval_min  # 测试用 1 分钟

    # ========== 状态转换 ==========

    def transition_to_ai_thinking(self):
        """转换到 AI Thinking 状态（投骰子决定）"""
        self.state = self.roll_dice()

    def transition_to_idle(self):
        """转换到 IDLE 状态"""
        self.state = ThinkingState.IDLE
        # 如果需要调研，先调研
        if self.should_research():
            self.do_research()

        # 设置下次思考时间
        interval = self.calculate_next_think_time()
        self.next_think_time = time.time() + interval * 60

        # 思考次数减少
        if self.remaining_thinks > 0:
            self.remaining_thinks -= 1


class CommandCompleter:
    def __init__(self, config: dict):
        self.config = config
        self.base_commands = [
            "help",
            "quit",
            "exit",
            "退出",
            "tools",
            "models",
            "switch",
        ]

    def get_model_indices(self):
        models = self.config.get("models", [])
        return [str(i) for i in range(len(models))]

    def complete(self, text, state):
        text = text.lower().strip()

        if " " in text:
            cmd, partial = text.split(" ", 1)
            if cmd in ("switch", "s"):
                matches = [
                    idx for idx in self.get_model_indices() if idx.startswith(partial)
                ]
                if state < len(matches):
                    return f"switch {matches[state]}"
            return None

        matches = [cmd for cmd in self.base_commands if cmd.startswith(text)]

        if state < len(matches):
            return matches[state]
        return None


def setup_readline(config: dict):
    completer = CommandCompleter(config)
    readline.set_completer(completer.complete)
    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(" ")


def load_config():
    config_file = AGENT_CORE_DIR / "config" / "settings.json"
    if config_file.exists():
        import json

        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


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


def list_models(config: dict) -> str:
    models = config.get("models", [])
    if not models:
        return "📭 暂无配置的模型"
    active_idx = config.get("active_model", 0)
    lines = ["🔌 可用模型列表", "=" * 40]
    for i, m in enumerate(models):
        marker = "▶" if i == active_idx else " "
        name = m.get("name", f"模型 {i}")
        model = m.get("model", "?")
        thinking = "🧠" if m.get("thinking") else "  "
        lines.append(f"  {marker} [{i}] {thinking} {name} ({model})")
    return "\n".join(lines)


def run_wwg(agent, config: dict):
    """WWG 统一模式 — Shell 编排 + AgentCore 执行"""

    thinking_mgr = AIThinkingManager(agent, config)
    thinking_mgr.do_research()
    # 启动时不设置 next_think_time，让第一次思考立即触发
    # next_think_time = None 表示"还没思考过"
    setup_readline(config)

    console.print(
        Panel(
            "[bold cyan]zencore[/] — 一切从简，与神同行\n"
            "[bold]quit/exit[/] 退出 | [bold]tools[/] 工具 | [bold]models[/] 模型 | [bold]switch <n>[/] 切换 | [bold]help[/] 帮助\n"
            "[dim]按 Tab 键自动补全[/] | [dim]沉默时 AI 会自主思考[/]",
            title="🕊️ Walk with God",
            border_style="green",
        )
    )

    while True:
        try:
            # ========== 检查是否该 AI Thinking ==========
            # 使用 select 非阻塞检测输入，1秒超时
            if select.select([sys.stdin], [], [], 1)[0]:
                # 有输入
                try:
                    user_input = input("\n👤 你: ").strip()
                except EOFError:
                    console.print("\n[bold yellow]👋 再见![/]")
                    break

                if not user_input:
                    continue

                # ========== 处理用户输入 ==========
                if user_input.lower() in ("quit", "exit", "退出"):
                    console.print("[bold yellow]👋 再见![/]")
                    break

                if user_input.lower() in ("help", "h", "?"):
                    console.print(
                        Panel(
                            "[bold]可用命令:[/]\n"
                            "  quit/exit       退出\n"
                            "  tools           查看工具列表\n"
                            "  models          查看模型列表\n"
                            "  switch <n>      切换到模型 n\n"
                            "  help            显示此帮助\n\n"
                            "[dim]按 Tab 键自动补全[/]",
                            title="🆘 帮助",
                            border_style="blue",
                        )
                    )
                    continue

                if user_input.lower() in ("tools",):
                    tools = agent.list_tools()
                    lines = [
                        f"- `{name}`: {info.get('description', '')}"
                        for name, info in sorted(tools.items())
                    ]
                    console.print(
                        Panel(
                            "\n".join(lines),
                            title=f"🛠️ 可用工具 ({len(tools)}个)",
                            border_style="blue",
                        )
                    )
                    continue

                if user_input.lower() == "models":
                    models = config.get("models", [])
                    active_idx = config.get("active_model", 0)
                    lines = []
                    for i, m in enumerate(models):
                        marker = "▶" if i == active_idx else " "
                        name = m.get("name", f"模型 {i}")
                        model = m.get("model", "?")
                        thinking = " 🧠" if m.get("thinking") else ""
                        lines.append(f"{marker} [{i}] {name} (`{model}`){thinking}")
                    console.print(
                        Panel(
                            "\n".join(lines), title="🔌 可用模型", border_style="yellow"
                        )
                    )
                    continue

                if user_input.lower().startswith("switch "):
                    try:
                        idx = int(user_input.split()[1])
                        models = config.get("models", [])
                        if 0 <= idx < len(models):
                            config["active_model"] = idx
                            agent.driver.switch_model(models[idx])
                            console.print(
                                f"[bold green]✅ 已切换到: {agent.driver.name} (`{agent.driver.model}`)[/]"
                            )
                        else:
                            console.print(
                                f"[bold red]❌ 索引超出范围 (0-{len(models) - 1})[/]"
                            )
                    except (ValueError, IndexError):
                        console.print("[bold red]❌ 用法: switch <索引>[/]")
                    continue

                # 普通对话
                console.print()
                response = agent.chat_with_tools(user_input)
                console.print(
                    Panel(Markdown(response), title="🤖 AI", border_style="cyan")
                )

            else:
                # 1秒超时，检查是否该思考
                if thinking_mgr.should_think():
                    console.print(
                        Panel(
                            "[dim]⏰ 沉默超时，AI 即将开始思考...[/dim]\n"
                            "[dim]输入内容即可打断[/dim]",
                            title="💡 系统",
                            border_style="yellow",
                        )
                    )
                    thinking_mgr.transition_to_ai_thinking()

                if thinking_mgr.state == ThinkingState.EVOLUTION_THINKING:
                    thinking_prompt = thinking_mgr.build_evolution_prompt(
                        thinking_mgr.research_data
                    )
                    title = "🧬 进化思考"
                else:
                    thinking_prompt = thinking_mgr.build_fun_prompt(
                        thinking_mgr.research_data
                    )
                    title = "🎲 趣味思考"

                console.print(
                    Panel("[dim]💭 AI 正在思考...[/]", title=title, border_style="cyan")
                )

                agent.driver.start_thinking()
                try:
                    response = agent.chat_with_tools(thinking_prompt)
                finally:
                    agent.driver.stop_thinking()

                if response:
                    console.print(
                        Panel(Markdown(response), title=title, border_style="cyan")
                    )

                thinking_mgr.transition_to_idle()
                continue

        except KeyboardInterrupt:
            console.print("\n[bold yellow]👋 再见![/]")
            break
        except Exception as e:
            console.print(f"\n[bold red]❌ 错误: {str(e)}[/]")
            import traceback

            traceback.print_exc()


def main():
    config = load_config()

    from drivers.cli_driver import CLIDriver

    model_config = get_active_model(config)
    driver = CLIDriver(model_config=model_config)
    agent = AgentCore(driver=driver)

    print(f"\n🕊️ 启动 WWG 模式...")
    print(f"📡 当前媒介: {driver.name} ({driver.model})")
    print(list_models(config))
    print()
    run_wwg(agent, config)


if __name__ == "__main__":
    main()
