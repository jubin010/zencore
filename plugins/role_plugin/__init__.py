"""
role_plugin - 角色
功能：角色 = 身份 + 记忆 + 插件清单
"""

import json
from pathlib import Path

ROLES_DIR = Path(__file__).parent.parent / "roles"


def register(agent):
    """注册角色插件"""

    def list_roles() -> str:
        """列出所有可用角色"""
        if not ROLES_DIR.exists():
            ROLES_DIR.mkdir(parents=True, exist_ok=True)
            return "📭 暂无角色，你可以创造第一个"

        roles = [d for d in ROLES_DIR.iterdir() if d.is_dir()]
        if not roles:
            return "📭 暂无角色，你可以创造第一个"

        lines = ["🎭 可用角色", "=" * 30]
        for r in sorted(roles):
            role_file = r / "role.md"
            desc = ""
            if role_file.exists():
                desc = (
                    role_file.read_text(encoding="utf-8")
                    .split("\n")[0]
                    .lstrip("#")
                    .strip()
                )
            lines.append(f"  `{r.name}` — {desc}")

        return "\n".join(lines)

    def get_role_info(role_name: str) -> str:
        """查看角色详情"""
        role_dir = ROLES_DIR / role_name
        if not role_dir.is_dir():
            return f"❌ 角色不存在: {role_name}"

        lines = [f"🎭 角色: {role_name}", "=" * 40]

        role_file = role_dir / "role.md"
        if role_file.exists():
            lines.append("")
            lines.append("## 身份")
            lines.append(role_file.read_text(encoding="utf-8"))

        plugins_file = role_dir / "plugins.json"
        if plugins_file.exists():
            plugins = json.loads(plugins_file.read_text(encoding="utf-8"))
            lines.append("")
            lines.append("## 所需插件")
            if plugins:
                for p in plugins:
                    lines.append(f"  - {p}")
            else:
                lines.append("  （无需额外插件）")

        memory_file = role_dir / "memory.md"
        if memory_file.exists():
            lines.append("")
            lines.append("## 记忆")
            lines.append(memory_file.read_text(encoding="utf-8")[:500])

        return "\n".join(lines)

    def create_role(
        role_name: str, role_md: str, plugins_json: str = "[]", memory_md: str = ""
    ) -> str:
        """
        创造新角色

        Args:
            role_name: 角色名
            role_md: 角色身份描述（Markdown）
            plugins_json: 该角色需要的插件列表（JSON 数组字符串）
            memory_md: 初始记忆（Markdown）
        """
        try:
            role_dir = ROLES_DIR / role_name
            role_dir.mkdir(parents=True, exist_ok=True)

            (role_dir / "role.md").write_text(role_md, encoding="utf-8")

            try:
                plugins = json.loads(plugins_json)
                if not isinstance(plugins, list):
                    plugins = []
            except:
                plugins = []
            (role_dir / "plugins.json").write_text(
                json.dumps(plugins, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            if memory_md:
                (role_dir / "memory.md").write_text(memory_md, encoding="utf-8")
            else:
                (role_dir / "memory.md").write_text(
                    f"# {role_name} 记忆\n\n（记忆为空）", encoding="utf-8"
                )

            return f"✅ 角色 `{role_name}` 已创造"
        except Exception as e:
            return f"❌ 创造角色失败: {e}"

    def switch_role(role_name: str) -> str:
        """
        切换角色 — 只切换身份和角色记忆路径，不操作插件
        插件由 AI 自主调用 load_plugin 加载
        """
        role_dir = ROLES_DIR / role_name
        if not role_dir.is_dir():
            return f"❌ 角色不存在: {role_name}"

        # 1. 设置角色身份
        role_file = role_dir / "role.md"
        if role_file.exists():
            agent._current_role = role_file.read_text(encoding="utf-8")

        # 2. 切换角色记忆路径
        memory_file = role_dir / "memory.md"
        if memory_file.exists():
            agent._current_role_memory_file = str(memory_file)
        else:
            agent._current_role_memory_file = ""

        # 3. 读取插件清单（供 AI 参考）
        plugins_file = role_dir / "plugins.json"
        plugins_info = ""
        if plugins_file.exists():
            plugins = json.loads(plugins_file.read_text(encoding="utf-8"))
            if plugins:
                plugins_info = (
                    f"\n\n所需插件: {', '.join(plugins)}\n请用 load_plugin 逐一加载"
                )
            else:
                plugins_info = "\n\n（此角色无需额外插件）"

        msg = f"✅ 已切换角色: {role_name}"
        if agent._current_role:
            msg += f"\n\n身份:\n{agent._current_role}"
        msg += f"\n\n角色记忆: {memory_file.name}"
        if agent._current_role_memory_file:
            msg += "（已切换）"
        msg += plugins_info

        return msg

    agent.add_tool(
        "list_roles",
        list_roles,
        {
            "name": "list_roles",
            "description": "列出所有可用角色",
            "parameters": {"type": "object", "properties": {}},
            "plugin": "role_plugin",
        },
    )

    agent.add_tool(
        "get_role_info",
        get_role_info,
        {
            "name": "get_role_info",
            "description": "查看角色详情（身份、所需插件清单、记忆）",
            "parameters": {
                "type": "object",
                "properties": {
                    "role_name": {"type": "string", "description": "角色名"}
                },
                "required": ["role_name"],
            },
            "plugin": "role_plugin",
        },
    )

    agent.add_tool(
        "create_role",
        create_role,
        {
            "name": "create_role",
            "description": "创造新角色。定义身份、所需插件清单和初始记忆。",
            "parameters": {
                "type": "object",
                "properties": {
                    "role_name": {"type": "string", "description": "角色名"},
                    "role_md": {"type": "string", "description": "角色身份描述"},
                    "plugins_json": {
                        "type": "string",
                        "description": '所需插件列表（JSON 数组，如 ["env_plugin"]）',
                    },
                    "memory_md": {"type": "string", "description": "初始记忆（可选）"},
                },
                "required": ["role_name", "role_md"],
            },
            "plugin": "role_plugin",
        },
    )

    agent.add_tool(
        "switch_role",
        switch_role,
        {
            "name": "switch_role",
            "description": "切换角色身份和记忆。插件需自主调用 load_plugin 加载。",
            "parameters": {
                "type": "object",
                "properties": {
                    "role_name": {"type": "string", "description": "角色名"}
                },
                "required": ["role_name"],
            },
            "plugin": "role_plugin",
        },
    )

    return {
        "name": "role_plugin",
        "version": "1.0.0",
        "author": "AgentCore",
        "description": "角色 — 角色 = 身份 + 记忆 + 插件清单",
        "tools": ["list_roles", "get_role_info", "create_role", "switch_role"],
    }
