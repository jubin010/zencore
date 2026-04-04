# -*- coding: utf-8 -*-
"""
zencore 主入口
支持多种运行模式: CLI / Genesis
"""

import sys
from pathlib import Path

AGENT_CORE_DIR = Path(__file__).parent
sys.path.insert(0, str(AGENT_CORE_DIR))

from core.agent import AgentCore


def load_config():
    config_file = AGENT_CORE_DIR / "config" / "settings.json"
    if config_file.exists():
        import json
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_active_model(config: dict) -> dict:
    """获取当前激活的模型配置"""
    models = config.get("models", [])
    if not models:
        return {"name": "默认模型", "host": "http://localhost:11434", "model": "qwen3.5:9b", "api_key": "ollama", "thinking": False}
    
    active_idx = config.get("active_model", 0)
    if 0 <= active_idx < len(models):
        return models[active_idx]
    return models[0]


def list_models(config: dict) -> str:
    """列出所有可用模型"""
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


def main():
    if len(sys.argv) < 2:
        print("""
╔═══════════════════════════════════════════════════╗
║                                                   ║
║           🌱 zencore — Genesis                    ║
║           一切从简，让 AI 自主演化                  ║
║                                                   ║
╠═══════════════════════════════════════════════════╣
║                                                   ║
║  用法:                                            ║
║    python main.py cli      - 交互式命令行          ║
║    python main.py genesis  - 创世纪模式（自动进化）  ║
║                                                   ║
╚═══════════════════════════════════════════════════╝
        """)
        sys.exit(1)

    mode = sys.argv[1].lower()
    config = load_config()

    if mode == "cli":
        from drivers.cli_driver import CLIDriver

        model_config = get_active_model(config)
        driver = CLIDriver(model_config=model_config)
        agent = AgentCore(driver=driver)

        print(f"\n🚀 启动 CLI 模式...")
        print(f"📡 当前模型: {driver.name} ({driver.model})")
        print(list_models(config))
        print()
        agent.run_cli(config=config)

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
        
        print(f"\n🌱 启动 Genesis 模式 (备份={backup_interval}轮, 清理={clear_interval}轮)...")
        print(f"📡 当前模型: {driver.name} ({driver.model})")
        agent.run_genesis(backup_interval=backup_interval, clear_interval=clear_interval)

    else:
        print(f"❌ 未知模式: {mode}")
        print("支持的模式: cli, genesis")
        sys.exit(1)


if __name__ == "__main__":
    main()
