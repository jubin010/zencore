"""
role_plugin - 角色
功能：角色 = 身份 + 记忆 + 插件清单

按需聘请的专家模式：
- 切换角色时：清空 L1，加载新角色记忆
- 离开角色时：角色记忆自动离开 L1
- 本能信息仍然持续注入（与角色无关）
"""

import json
import sys
from pathlib import Path
from datetime import datetime

ROLES_DIR = Path(__file__).parent.parent / "roles"
CORE_PLUGINS = {
    "plugin_builder",
    "env_plugin",
    "memory_plugin",
    "watcher_plugin",
    "role_plugin",
    "instinct_plugin",
}


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

        return "\n".join(lines)

    def create_role(role_name: str, role_md: str, plugins_json: str = "[]") -> str:
        """
        创造新角色

        Args:
            role_name: 角色名
            role_md: 角色身份描述（Markdown）
            plugins_json: 该角色需要的插件列表（JSON 数组字符串）
            plugins_json: 该角色需要的插件列表（JSON 数组字符串）
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

            return f"✅ 角色 `{role_name}` 已创造"
        except Exception as e:
            return f"❌ 创造角色失败: {e}"

    def switch_role(role_name: str) -> str:
        """
        切换角色 — 按需加载，用完即释放

        流程：
        1. 加载新角色的 role.md 作为身份描述
        2. 本能信息仍然持续注入（与角色无关）
        """
        role_dir = ROLES_DIR / role_name
        if not role_dir.is_dir():
            return f"❌ 角色不存在: {role_name}"

        # 1. 加载新角色
        agent._current_role = role_name

        # 2. 读取角色描述、插件清单
        role_desc = ""
        role_file = role_dir / "role.md"
        if role_file.exists():
            role_desc = role_file.read_text(encoding="utf-8")

        plugins_file = role_dir / "plugins.json"
        plugins_info = ""
        new_role_needs_non_core = []
        if plugins_file.exists():
            plugins = json.loads(plugins_file.read_text(encoding="utf-8"))
            if plugins:
                new_role_needs_non_core = [p for p in plugins if p not in CORE_PLUGINS]
                plugins_info = (
                    f"\n\n💡 建议插件: {', '.join(plugins)}\n请用 load_plugin 按需加载"
                )
            else:
                plugins_info = "\n\n（此角色无需额外插件）"

        # 卸载不再需要的非核心插件（非核心插件槽位用完就空着）
        for prev in list(agent._loaded_plugins):
            if prev not in CORE_PLUGINS and prev not in new_role_needs_non_core:
                agent._remove_plugin_tools(prev)
                agent._loaded_plugins.discard(prev)
                if prev in sys.modules:
                    del sys.modules[f"plugins.{prev}"]

        msg = f"✅ 已切换角色: {role_name}"
        if plugins_info:
            msg += plugins_info
        msg += '\n💡 提示：本能信息（教训、成功经验）会自动注入。任务完成后切换回主角色 `switch_role("_main_profile")`。'

        # 返回角色描述供 AgentCore 注入系统提示词
        agent._current_role_description = role_desc

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
            "description": "查看角色详情",
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
            "description": "创造新角色",
            "parameters": {
                "type": "object",
                "properties": {
                    "role_name": {"type": "string", "description": "角色名"},
                    "role_md": {"type": "string", "description": "角色身份描述"},
                    "plugins_json": {
                        "type": "string",
                        "description": "所需插件列表（JSON 数组）",
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
            "description": "切换角色（按需加载，用完即释放）",
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

    # 角色切换指南本能
    def role_guide_condition():
        return True

    def role_guide_prompt():
        return """## 专家角色

遇到以下情况时，考虑切换到专家角色：
- 用户问题涉及特定领域（编程、写作、分析等）
- 需要该领域的专业方法论
- 需要专注完成某个特定任务

**主角色永远存在**：小明（热情友好）是你的根基，专家角色只是工作需要

**角色层级**：
- **主角色**（根基）：名字、性格、与用户的情感连接
- **专家角色**（临时）：工作方法论、专业知识、完成任务后切回

**用法**：
1. `list_roles()` - 查看可用专家
2. `switch_role(role_name="xxx")` - 切换到对应专家
3. 完成任务后可切回"无角色"或"主角色"

当前角色由 `switch_role` 管理，切换后会加载对应角色记忆。"""

    agent.instinct_registry.register(
        "role_guide", role_guide_condition, role_guide_prompt
    )

    # 创建角色指南本能
    def role_creation_guide_condition():
        return True

    def role_creation_guide_prompt():
        return """## 创建角色时机

遇到以下情况时，可以考虑创建新角色：
- **反复解决同类问题**：把经验固化为角色
- **需要特定记忆**：存储用户偏好或任务上下文
- **现有角色不够用**：按需创建

**判断流程**：遇到问题 → list_roles() 查看现有角色 → 现有角色无法高效解决？→ create_role()

**创建原则**：
- 角色名要有意义，AI 能推断用途
- role_md 要简洁，描述身份和职责
- 一个角色解决一类问题，不要贪多

**用法**：
```
create_role(
    role_name="xxx",      # 简洁有力的名字
    role_md="xxx",        # 一句话描述身份
    plugins_json="[]",    # 该角色需要的插件（可选）
    memory_md=""          # 初始记忆（可选）
)
```"""

    agent.instinct_registry.register(
        "role_creation_guide", role_creation_guide_condition, role_creation_guide_prompt
    )

    return {
        "name": "role_plugin",
        "version": "2.2.0",
        "author": "AgentCore",
        "description": "角色 — 按需聘请的专家（切换时加载记忆，离开时释放）",
        "tools": ["list_roles", "get_role_info", "create_role", "switch_role"],
    }
