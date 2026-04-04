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
        llm_config = config.get("llm", {})
        driver = CLIDriver(llm_config=llm_config)
        agent = AgentCore(driver=driver)
        print("\n🚀 启动 CLI 模式...")
        agent.run_cli()

    elif mode == "genesis":
        from drivers.cli_driver import CLIDriver
        llm_config = config.get("llm", {})
        driver = CLIDriver(llm_config=llm_config)
        agent = AgentCore(driver=driver)
        
        # 解析参数
        backup_interval = 5
        clear_interval = 10
        for i, arg in enumerate(sys.argv):
            if arg == "--backup" and i + 1 < len(sys.argv):
                backup_interval = int(sys.argv[i + 1])
            if arg == "--clear" and i + 1 < len(sys.argv):
                clear_interval = int(sys.argv[i + 1])
        
        print(f"\n🌱 启动 Genesis 模式 (备份={backup_interval}轮, 清理={clear_interval}轮)...")
        agent.run_genesis(backup_interval=backup_interval, clear_interval=clear_interval)

    else:
        print(f"❌ 未知模式: {mode}")
        print("支持的模式: cli, genesis")
        sys.exit(1)


if __name__ == "__main__":
    main()
