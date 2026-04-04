"""
memory_plugin - 记忆
功能：记忆的存在

记忆存放在 memory.md 中，纯 Markdown 格式。
AI 自主维护记忆的内容和结构。
操作记忆？用文件工具。
"""

from pathlib import Path

MEMORY_FILE = Path(__file__).parent / "memory.md"


def register(agent):
    """注册记忆插件 — 零工具，纯存在"""
    return {
        "name": "memory_plugin",
        "version": "1.0.0",
        "author": "AgentCore",
        "description": "记忆 — AI 的持久化记忆，存放在 memory.md 中",
        "tools": [],
    }
