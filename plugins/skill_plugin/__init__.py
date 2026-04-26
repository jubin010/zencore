"""
skill_plugin - 技能管理
功能：管理 skills/ 目录下的技能装备

主角色由 memory_plugin/main_role.md 始终注入，技能只是叠加的专业能力。
"""

from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent / "skills"


def register(agent):
    """注册技能插件"""

    def list_skills() -> str:
        """列出所有可用技能"""
        if not SKILLS_DIR.exists():
            return "📭 暂无技能目录"

        skills = [d for d in SKILLS_DIR.iterdir() if d.is_dir()]
        if not skills:
            return "📭 暂无技能，你可以创造第一个"

        lines = ["🎭 可用技能", "=" * 30]
        for s in sorted(skills):
            skill_file = s / "skill.md"
            desc = ""
            if skill_file.exists():
                desc = (
                    skill_file.read_text(encoding="utf-8")
                    .split("\n")[0]
                    .lstrip("#")
                    .strip()
                )
            lines.append(f"  `{s.name}` — {desc}")

        return "\n".join(lines)

    def get_skill_info(skill_name: str) -> str:
        """查看技能详情"""
        skill_dir = SKILLS_DIR / skill_name
        if not skill_dir.is_dir():
            return f"❌ 技能不存在: {skill_name}"

        lines = [f"🎭 技能: {skill_name}", "=" * 40]

        skill_file = skill_dir / "skill.md"
        if skill_file.exists():
            lines.append("")
            lines.append("## 描述")
            lines.append(skill_file.read_text(encoding="utf-8"))

        plugins_file = skill_dir / "plugins.json"
        if plugins_file.exists():
            plugins = json.loads(plugins_file.read_text(encoding="utf-8"))
            if plugins:
                lines.append(f"\n💡 建议插件: {', '.join(plugins)}")

        return "\n".join(lines)

    def create_skill(skill_name: str, skill_md: str) -> str:
        """创造新技能"""
        try:
            skill_dir = SKILLS_DIR / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)

            (skill_dir / "skill.md").write_text(skill_md, encoding="utf-8")

            return f"✅ 技能 `{skill_name}` 已创造"
        except Exception as e:
            return f"❌ 创造技能失败: {e}"

    def equip_skill(skill_name: str) -> str:
        """装备技能"""
        skill_dir = SKILLS_DIR / skill_name
        if not skill_dir.is_dir():
            return f"❌ 技能不存在: {skill_name}"

        agent._current_role = skill_name

        skill_desc = ""
        skill_file = skill_dir / "skill.md"
        if skill_file.exists():
            skill_desc = skill_file.read_text(encoding="utf-8")

        agent._current_role_description = skill_desc

        return f"✅ 已装备技能: {skill_name}"

    agent.add_tool(
        "list_skills",
        list_skills,
        {
            "name": "list_skills",
            "description": "列出所有可用技能",
            "parameters": {"type": "object", "properties": {}},
            "plugin": "skill_plugin",
        },
    )

    agent.add_tool(
        "get_skill_info",
        get_skill_info,
        {
            "name": "get_skill_info",
            "description": "查看技能详情。参数skill_name是技能文件夹名称，如developer、auditor等",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {"type": "string", "description": "技能名称（必填），如developer、auditor"}
                },
                "required": ["skill_name"],
            },
            "plugin": "skill_plugin",
        },
    )

    agent.add_tool(
        "create_skill",
        create_skill,
        {
            "name": "create_skill",
            "description": "创造新技能",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {"type": "string", "description": "技能名"},
                    "skill_md": {"type": "string", "description": "技能描述"},
                },
                "required": ["skill_name", "skill_md"],
            },
            "plugin": "skill_plugin",
        },
    )

    agent.add_tool(
        "equip_skill",
        equip_skill,
        {
            "name": "equip_skill",
            "description": "装备技能",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {"type": "string", "description": "技能名"}
                },
                "required": ["skill_name"],
            },
            "plugin": "skill_plugin",
        },
    )

    return {
        "name": "skill_plugin",
        "version": "2.0.0",
        "author": "AgentCore",
        "description": "技能管理 — 装备/卸下专业能力",
        "tools": ["list_skills", "get_skill_info", "create_skill", "equip_skill"],
    }