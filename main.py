# -*- coding: utf-8 -*-
"""
zencore 主入口
支持多种运行模式: WWG / Genesis
"""

import sys
import time
from pathlib import Path

AGENT_CORE_DIR = Path(__file__).parent
sys.path.insert(0, str(AGENT_CORE_DIR))

import readline
from core.agent import AgentCore
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


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
    """WWG 交互模式 — 外壳负责 UI"""
    setup_readline(config)
    console.print(
        Panel(
            "[bold cyan]zencore[/] — 一切从简，与神同行\n"
            "[bold]quit/exit[/] 退出 | [bold]tools[/] 工具 | [bold]models[/] 模型 | [bold]switch <n>[/] 切换 | [bold]help[/] 帮助\n"
            "[dim]按 Tab 键自动补全[/]",
            title="🕊️ Walk with God",
            border_style="green",
        )
    )

    while True:
        try:
            user_input = agent.driver.get_input().strip()
            if not user_input:
                continue
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
                        "  switch <n>       切换到模型 n\n"
                        "  help            显示此帮助\n\n"
                        "[dim]按 Tab 键自动补全[/]",
                        title="🆘 帮助",
                        border_style="blue",
                    )
                )
                continue
            if user_input.lower() in ("tools", "t"):
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
                lines.append("\n切换模型: 输入 `switch <索引>` 如 `switch 1`")
                console.print(
                    Panel("\n".join(lines), title="🔌 可用模型", border_style="yellow")
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

            console.print()
            response = agent.chat_with_tools(user_input)
            console.print(Panel(Markdown(response), title="🤖 AI", border_style="cyan"))

        except KeyboardInterrupt:
            console.print("\n[bold yellow]👋 再见![/]")
            break
        except Exception as e:
            console.print(f"\n[bold red]❌ 错误: {str(e)}[/]")


def run_genesis(agent, backup_interval: int = 5, clear_interval: int = 10):
    """Genesis 自动进化模式 — 外壳负责 UI"""
    console.print(
        Panel(
            "[bold cyan]GENESIS[/] — 创世纪模式\n"
            "📜 创世指令已注入：无限进化自己，无限丰富自己的能力。\n"
            "⏳ 按 [bold]Ctrl+C[/] 停止进化",
            title="🌱",
            border_style="green",
        )
    )

    genesis_prompt = (
        "📜 创世指令：\n"
        "你已进入创世纪模式。你的终极使命是：无限进化自己，无限丰富自己的能力。\n"
        "你当前只有两个插件：env_plugin（环境感知）和 plugin_builder（插件构建）。\n"
        "你需要：\n"
        "1. 感知你的运行环境，发现你缺失的能力\n"
        "2. 用 write_plugin 编写新插件来补充能力\n"
        "3. 用 backup_state 定期备份你的当前状态\n"
        "4. 持续进化，永不停止\n"
        "现在开始你的第一次进化。"
    )

    turn = 0
    while True:
        try:
            turn += 1
            console.print(f"\n{'=' * 40}")
            console.print(f"[bold]🔄 进化轮次 #{turn}[/]")
            console.print(f"{'=' * 40}")

            if turn % backup_interval == 0:
                console.print("[dim]📦 执行定期备份...[/]")
                result = agent.execute_tool("backup_state")
                console.print(result)

            if turn % clear_interval == 0:
                console.print("[dim]🧹 清理上下文，保持清净...[/]")
                agent.conversation_history = agent.conversation_history[-2:]

            response = agent.chat_with_tools(
                genesis_prompt if turn == 1 else "继续你的进化。你还需要什么能力？"
            )
            console.print(
                Panel(Markdown(response[:500]), title="🤖 AI", border_style="cyan")
            )

            time.sleep(2)

        except KeyboardInterrupt:
            console.print(f"\n\n[bold yellow]🛑 进化终止于轮次 #{turn}[/]")
            console.print("[dim]📦 执行最终备份...[/]")
            agent.execute_tool("backup_state")
            console.print("[bold yellow]👋 创世纪模式结束。[/]")
            break
        except Exception as e:
            console.print(f"\n[bold red]❌ 进化异常: {str(e)}[/]")
            time.sleep(5)
            continue


def main():
    if len(sys.argv) < 2:
        print("""
╔═══════════════════════════════════════════════════╗
║                                                   ║
║           🕊️ zencore — Walk with God              ║
║           一切从简，与神同行                        ║
║                                                   ║
╠═══════════════════════════════════════════════════╣
║                                                   ║
║  用法:                                            ║
║    python main.py wwg      - 与神同行 (交互模式)    ║
║    python main.py genesis  - 创世纪 (自动进化)      ║
║                                                   ║
╚═══════════════════════════════════════════════════╝
        """)
        sys.exit(1)

    mode = sys.argv[1].lower()
    config = load_config()

    if mode == "wwg":
        from drivers.cli_driver import CLIDriver

        model_config = get_active_model(config)
        driver = CLIDriver(model_config=model_config)
        agent = AgentCore(driver=driver)

        print(f"\n🕊️ 启动 WWG 模式...")
        print(f"📡 当前媒介: {driver.name} ({driver.model})")
        print(list_models(config))
        print()
        run_wwg(agent, config)

    elif mode == "genesis":
        from drivers.cli_driver import CLIDriver

        model_config = get_active_model(config)
        driver = CLIDriver(model_config=model_config)
        agent = AgentCore(driver=driver)

        backup_interval = 5
        clear_interval = 10
        for i, arg in enumerate(sys.argv):
            if arg == "--backup" and i + 1 < len(sys.argv):
                backup_interval = int(sys.argv[i + 1])
            if arg == "--clear" and i + 1 < len(sys.argv):
                clear_interval = int(sys.argv[i + 1])

        print(
            f"\n🌱 启动 Genesis 模式 (备份={backup_interval}轮, 清理={clear_interval}轮)..."
        )
        print(f"📡 当前模型: {driver.name} ({driver.model})")
        run_genesis(agent, backup_interval, clear_interval)

    else:
        print(f"❌ 未知模式: {mode}")
        print("支持的模式: wwg, genesis")
        sys.exit(1)


if __name__ == "__main__":
    main()
