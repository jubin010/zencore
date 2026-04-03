# -*- coding: utf-8 -*-
"""
AgentCore 主入口
支持多种运行模式: CLI / Web
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
AGENT_CORE_DIR = Path(__file__).parent
sys.path.insert(0, str(AGENT_CORE_DIR))

from core.agent import AgentCore


def load_config():
    """加载配置"""
    config_file = AGENT_CORE_DIR / "config" / "settings.json"
    
    if config_file.exists():
        import json
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # 默认配置
    return {
        "llm_provider": "ollama",
        "llm_model": "qwen2.5:7b",
        "llm_base_url": "http://localhost:11434",
        "max_history": 50
    }


def main():
    """主入口"""
    if len(sys.argv) < 2:
        print("""
╔═══════════════════════════════════════════════════╗
║                                                   ║
║           🤖 AgentCore AI智能体                   ║
║           一切皆为插件，AI可插拔                    ║
║                                                   ║
╠═══════════════════════════════════════════════════╣
║                                                   ║
║  用法:                                            ║
║    python main.py cli    - 命令行模式              ║
║    python main.py web    - Web模式                 ║
║                                                   ║
║  示例:                                            ║
║    python main.py cli                            ║
║    python main.py web                            ║
║    python main.py web --host 127.0.0.1 --port 8080║
║                                                   ║
╚═══════════════════════════════════════════════════╝
        """)
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    config = load_config()
    
    # 初始化AgentCore
    agent = AgentCore(config=config)
    
    if mode == "cli":
        print("\n🚀 启动 CLI 模式...")
        agent.run_cli()
    
    elif mode == "web":
        # 解析Web参数
        host = "0.0.0.0"
        port = 8080
        
        for i, arg in enumerate(sys.argv):
            if arg == "--host" and i + 1 < len(sys.argv):
                host = sys.argv[i + 1]
            if arg == "--port" and i + 1 < len(sys.argv):
                port = int(sys.argv[i + 1])
        
        print(f"\n🚀 启动 Web 模式 on {host}:{port}...")
        agent.run_web(host, port)
    
    else:
        print(f"❌ 未知模式: {mode}")
        print("支持的模式: cli, web")
        sys.exit(1)


if __name__ == "__main__":
    main()
