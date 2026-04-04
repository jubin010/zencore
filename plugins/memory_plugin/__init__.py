"""
memory_plugin - 记忆
功能：本体记忆 — 全局、跨角色、长期有效
"""

from pathlib import Path

MEMORY_FILE = Path(__file__).parent / "memory.md"


def register(agent):
    """注册本体记忆插件"""

    def read_global_memory() -> str:
        """读取全局记忆"""
        if MEMORY_FILE.exists():
            return MEMORY_FILE.read_text(encoding="utf-8")
        return "（全局记忆为空）"

    def write_global_memory(content: str) -> str:
        """覆盖写入全局记忆"""
        MEMORY_FILE.write_text(content, encoding="utf-8")
        return "✅ 全局记忆已更新"

    def append_global_memory(line: str) -> str:
        """追加一行到全局记忆"""
        mode = "a" if MEMORY_FILE.exists() else "w"
        with open(MEMORY_FILE, mode, encoding="utf-8") as f:
            f.write(line + "\n")
        return "✅ 已追加到全局记忆"

    agent.add_tool(
        "read_global_memory",
        read_global_memory,
        {
            "name": "read_global_memory",
            "description": "读取全局记忆（本体记忆）。所有角色共享的长期认知。",
            "parameters": {"type": "object", "properties": {}},
            "plugin": "memory_plugin",
        },
    )

    agent.add_tool(
        "write_global_memory",
        write_global_memory,
        {
            "name": "write_global_memory",
            "description": "覆盖写入全局记忆。用于更新用户画像、项目全局配置等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "完整的全局记忆内容（Markdown）",
                    }
                },
                "required": ["content"],
            },
            "plugin": "memory_plugin",
        },
    )

    agent.add_tool(
        "append_global_memory",
        append_global_memory,
        {
            "name": "append_global_memory",
            "description": "追加一行到全局记忆。用于记录跨角色的长期经验。",
            "parameters": {
                "type": "object",
                "properties": {
                    "line": {"type": "string", "description": "要追加的内容"}
                },
                "required": ["line"],
            },
            "plugin": "memory_plugin",
        },
    )

    return {
        "name": "memory_plugin",
        "version": "2.0.0",
        "author": "AgentCore",
        "description": "本体记忆 — 全局、跨角色、长期有效",
        "tools": ["read_global_memory", "write_global_memory", "append_global_memory"],
    }
