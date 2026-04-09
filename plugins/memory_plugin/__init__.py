"""
memory_plugin - 本体记忆
功能：全局、跨角色、长期有效的记忆操作

记忆层次架构：
- L2 缓存区：由本能管理，自动归档、自动淘汰
- 持久区：由 Librarian 管理，手动晋升、删除
"""

from pathlib import Path
from datetime import datetime

MEMORY_FILE = Path(__file__).parent / "memory.md"
LESSONS_FILE = Path(__file__).parent / "lessons.md"
WINS_FILE = Path(__file__).parent / "wins.md"

GLOBAL_LESSONS = LESSONS_FILE
GLOBAL_WINS = WINS_FILE

L2_CACHE_MARKER = "<!-- L2 -->"
L2_CACHE_SECTION = "## L2 缓存区\n"
PROMOTED_MARKER = "<!-- PROMOTED -->"
PROMOTED_SECTION = "## 持久记忆\n"

ROLES_DIR = Path(__file__).parent.parent / "roles"


def _compress_code_blocks(content: str) -> str:
    """仅压缩代码块为标记，保留文本原始内容"""
    if "```" not in content:
        return content
    lines = content.split("\n")
    compressed = []
    in_code = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            if in_code:
                lang = line.strip()[3:] or "code"
                compressed.append(f"[{lang}代码块]")
            continue
        if not in_code:
            compressed.append(line)
    return "\n".join(compressed)


def archive_to_l2(agent, indices: list) -> str:
    """
    手动归档指定对话条目到 L2 缓存（秘书筛选后使用，不做语义压缩）

    - 文本内容保留原始（仅压缩代码块为标记）
    - 索引为 conversation_history 中的位置
    - 归档后会从 conversation_history 删除这些条目
    """
    history = agent.conversation_history
    if not history:
        return "❌ 对话历史为空"

    valid_indices = []
    for idx in indices:
        if 0 <= idx < len(history):
            valid_indices.append(idx)

    if not valid_indices:
        return f"❌ 无效的索引，有效范围 0-{len(history) - 1}"

    valid_indices.sort(reverse=True)

    archived_entries = []
    for idx in valid_indices:
        msg = history[idx]
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        tool_name = msg.get("name", "")

        if role == "tool":
            formatted = f"- tool: {tool_name} → {_compress_code_blocks(content)}"
        else:
            formatted = f"- {role}: {_compress_code_blocks(content)}"

        archived_entries.append(
            {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "hits": 0,
                "content": formatted,
            }
        )

    timestamp = archived_entries[0]["timestamp"]
    entry_parts = [f"> 📅 {timestamp}", "> hits: 0"]
    for entry in archived_entries:
        entry_parts.append(entry["content"])

    archive_entry = "\n".join(entry_parts)

    l2_content, promoted_content = _get_memory_sections()
    l2_entries = _parse_entries(l2_content)
    l2_entries.append(
        {"timestamp": timestamp, "hits": 0, "lines": entry_parts, "section": "l2"}
    )

    new_l2_parts = []
    for entry in l2_entries:
        new_l2_parts.append("\n".join(entry["lines"]))
    new_l2_content = "\n\n".join(new_l2_parts)

    _write_memory_sections(new_l2_content, promoted_content)

    for idx in valid_indices:
        del history[idx]

    count = len(valid_indices)
    return f"✅ 已归档 {count} 条到 L2 缓存，对话历史已精简"


def _ensure_memory_structure():
    """确保记忆文件有正确的分区结构"""
    if not MEMORY_FILE.exists():
        MEMORY_FILE.write_text(
            "# 本体记忆\n\n"
            + L2_CACHE_MARKER
            + "\n"
            + L2_CACHE_SECTION
            + "（L2 缓存为空，归档会自动填充这里）\n\n"
            + PROMOTED_MARKER
            + "\n"
            + PROMOTED_SECTION
            + "（持久记忆区，由 Librarian 管理）\n",
            encoding="utf-8",
        )
        return

    content = MEMORY_FILE.read_text(encoding="utf-8")
    needs_update = False

    if L2_CACHE_MARKER not in content:
        content += (
            "\n\n" + L2_CACHE_MARKER + "\n" + L2_CACHE_SECTION + "（L2 缓存为空）\n"
        )
        needs_update = True

    if PROMOTED_MARKER not in content:
        content += (
            "\n\n" + PROMOTED_MARKER + "\n" + PROMOTED_SECTION + "（持久记忆区）\n"
        )
        needs_update = True

    if needs_update:
        MEMORY_FILE.write_text(content, encoding="utf-8")


def _get_memory_sections():
    """解析记忆文件的分区结构"""
    if not MEMORY_FILE.exists():
        return None, None

    content = MEMORY_FILE.read_text(encoding="utf-8")

    l2_start = content.find(L2_CACHE_MARKER)
    promoted_start = content.find(PROMOTED_MARKER)

    l2_content = ""
    promoted_content = ""

    if l2_start != -1:
        l2_section_start = content.find("\n", l2_start) + 1
        if promoted_start != -1:
            l2_content = content[l2_section_start:promoted_start].strip()
        else:
            l2_content = content[l2_section_start:].strip()

    if promoted_start != -1:
        promoted_section_start = content.find("\n", promoted_start) + 1
        promoted_content = content[promoted_section_start:].strip()

    return l2_content, promoted_content


def _write_memory_sections(l2_content: str, promoted_content: str):
    """写入记忆文件的分区结构"""
    _ensure_memory_structure()
    existing = MEMORY_FILE.read_text(encoding="utf-8")

    l2_marker_pos = existing.find(L2_CACHE_MARKER)
    promoted_marker_pos = existing.find(PROMOTED_MARKER)

    title = existing[:l2_marker_pos].strip()

    new_content = title + "\n\n" + L2_CACHE_MARKER + "\n" + L2_CACHE_SECTION
    if l2_content:
        new_content += "\n\n" + l2_content
    else:
        new_content += "（L2 缓存为空，归档会自动填充这里）\n"

    new_content += "\n\n" + PROMOTED_MARKER + "\n" + PROMOTED_SECTION
    if promoted_content:
        new_content += "\n\n" + promoted_content
    else:
        new_content += "（持久记忆区，由 Librarian 管理）\n"

    MEMORY_FILE.write_text(new_content, encoding="utf-8")


def _parse_entries(content: str) -> list:
    """解析记忆段落，返回 [{timestamp, hits, lines, section}] 列表"""
    if not content or "（为空" in content:
        return []

    entries = []
    current_entry = {"timestamp": "", "hits": 0, "lines": [], "section": "unknown"}

    for line in content.split("\n"):
        if line.startswith("> 📅 "):
            if current_entry["timestamp"] and current_entry["lines"]:
                entries.append(current_entry)
            timestamp = line[4:].strip()
            current_entry = {
                "timestamp": timestamp,
                "hits": 0,
                "lines": [line],
                "section": "unknown",
            }
        elif line.startswith("> hits: "):
            current_entry["hits"] = int(line.split("> hits: ")[1].strip())
        elif line.startswith("> 🕊️ "):
            if current_entry["timestamp"]:
                entries.append(current_entry)
            current_entry = {
                "timestamp": "已遗忘",
                "hits": 0,
                "lines": [line],
                "section": "evicted",
            }
        elif line.startswith("## "):
            section_name = line[3:].strip().rstrip("\n")
            current_entry["section"] = section_name
            current_entry["lines"].append(line)
        else:
            current_entry["lines"].append(line)

    if current_entry["timestamp"] and current_entry["lines"]:
        entries.append(current_entry)

    return entries


def register(agent):
    """注册本体记忆插件"""
    _ensure_memory_structure()

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

    def list_l2_cache() -> str:
        """列出 L2 缓存区的所有条目及其访问次数"""
        l2_content, _ = _get_memory_sections()
        entries = _parse_entries(l2_content)

        if not entries:
            return "📭 L2 缓存为空"

        lines = ["📦 L2 缓存区", "=" * 40]
        for i, entry in enumerate(entries):
            ts = entry.get("timestamp", "?")
            hits = entry.get("hits", 0)
            preview = entry["lines"][1] if len(entry["lines"]) > 1 else ""
            if preview.startswith("- "):
                preview = preview[2:60]
            lines.append(f"  [{i}] 📅 {ts} | 🔥 {hits}次 | {preview}...")

        lines.append(f"\n共 {len(entries)} 条缓存条目")
        lines.append("提示：检索记忆会使其 hits +1（升温）")
        return "\n".join(lines)

    def list_persistent_memory() -> str:
        """列出持久记忆区的所有条目"""
        _, promoted_content = _get_memory_sections()
        entries = _parse_entries(promoted_content)

        if not entries:
            return "📭 持久记忆区为空"

        lines = ["💾 持久记忆区", "=" * 40]
        for i, entry in enumerate(entries):
            ts = entry.get("timestamp", "?")
            preview = entry["lines"][1] if len(entry["lines"]) > 1 else ""
            if preview.startswith("- "):
                preview = preview[2:60]
            lines.append(f"  [{i}] 📅 {ts} | {preview}...")

        lines.append(f"\n共 {len(entries)} 条持久记忆")
        return "\n".join(lines)

    def heat_memory(index: int) -> str:
        """将 L2 缓存区指定索引的条目 hits +1（检索 = 访问 = 升温）"""
        l2_content, promoted_content = _get_memory_sections()
        entries = _parse_entries(l2_content)

        if not entries or index < 0 or index >= len(entries):
            return f"❌ 无效的索引 {index}"

        # 过滤掉已遗忘条目
        valid_entries = [e for e in entries if e["section"] != "evicted"]
        if index >= len(valid_entries):
            return f"❌ 索引 {index} 对应的条目已被遗忘"

        entry = valid_entries[index]
        entry["hits"] = entry.get("hits", 0) + 1

        # 重建 L2
        new_l2_parts = []
        for e in entries:
            if e["section"] != "evicted":
                new_l2_parts.append("\n".join(e["lines"]))

        new_l2_content = "\n\n".join(new_l2_parts)
        _write_memory_sections(new_l2_content, promoted_content)

        return f"🔥 记忆已升温：{entry['timestamp']} → hits={entry['hits']}"

    def promote_memory(index: int) -> str:
        """将 L2 缓存区指定索引的条目晋升到持久记忆区"""
        l2_content, promoted_content = _get_memory_sections()
        entries = _parse_entries(l2_content)

        if not entries or index < 0 or index >= len(entries):
            return f"❌ 无效的索引 {index}"

        valid_entries = [e for e in entries if e["section"] != "evicted"]
        if index >= len(valid_entries):
            return f"❌ 索引 {index} 对应的条目已被遗忘"

        entry = valid_entries[index]

        # 将 hits 最高的条目晋升
        promoted_entries = _parse_entries(promoted_content)
        promoted_entries.append(entry)

        # 重建持久区
        new_promoted_parts = []
        for e in promoted_entries:
            new_promoted_parts.append("\n".join(e["lines"]))
        new_promoted_content = "\n\n".join(new_promoted_parts)

        # 从 L2 移除
        valid_entries.pop(index)
        new_l2_parts = []
        for e in entries:
            if e["section"] == "evicted" or e in valid_entries:
                new_l2_parts.append("\n".join(e["lines"]))

        new_l2_content = "\n\n".join(new_l2_parts) if new_l2_parts else ""
        _write_memory_sections(new_l2_content, new_promoted_content)

        return f"⭐ 已晋升到持久区：{entry['timestamp']} (hits={entry['hits']})"

    def delete_from_l2(index: int) -> str:
        """从 L2 缓存区删除指定索引的条目"""
        l2_content, promoted_content = _get_memory_sections()
        entries = _parse_entries(l2_content)

        if not entries or index < 0 or index >= len(entries):
            return f"❌ 无效的索引 {index}"

        valid_entries = [e for e in entries if e["section"] != "evicted"]
        if index >= len(valid_entries):
            return f"❌ 索引 {index} 对应的条目已被遗忘"

        entry = valid_entries[index]
        entries.remove(entry)

        new_l2_parts = []
        for e in entries:
            new_l2_parts.append("\n".join(e["lines"]))

        new_l2_content = "\n\n".join(new_l2_parts) if new_l2_parts else ""
        _write_memory_sections(new_l2_content, promoted_content)

        return f"🗑️ 已从 L2 删除：{entry['timestamp']}"

    def delete_from_persistent(index: int) -> str:
        """从持久记忆区删除指定索引的条目"""
        l2_content, promoted_content = _get_memory_sections()
        entries = _parse_entries(promoted_content)

        if not entries or index < 0 or index >= len(entries):
            return f"❌ 无效的索引 {index}"

        entry = entries[index]
        entries.pop(index)

        new_promoted_parts = []
        for e in entries:
            new_promoted_parts.append("\n".join(e["lines"]))

        new_promoted_content = (
            "\n\n".join(new_promoted_parts) if new_promoted_parts else ""
        )
        _write_memory_sections(l2_content, new_promoted_content)

        return f"🗑️ 已从持久区删除：{entry['timestamp']}"

    def write_persistent_memory(content: str) -> str:
        """手动写入持久记忆（由 Librarian 整理后的内容）"""
        _, promoted_content = _get_memory_sections()
        new_entry = f"## 手动记录\n\n> 📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n{content}"

        if promoted_content and "（持久记忆区）" not in promoted_content:
            new_promoted_content = promoted_content + "\n\n" + new_entry
        else:
            new_promoted_content = new_entry

        _write_memory_sections("", new_promoted_content)
        return "💾 已写入持久记忆区"

    agent.add_tool(
        "read_global_memory",
        read_global_memory,
        {
            "name": "read_global_memory",
            "description": "读取全局记忆",
            "parameters": {"type": "object", "properties": {}},
            "plugin": "memory_plugin",
        },
    )

    agent.add_tool(
        "write_global_memory",
        write_global_memory,
        {
            "name": "write_global_memory",
            "description": "覆盖写入全局记忆",
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
            "description": "追加一行到全局记忆",
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

    agent.add_tool(
        "list_l2_cache",
        list_l2_cache,
        {
            "name": "list_l2_cache",
            "description": "列出 L2 缓存区的所有条目及其访问次数",
            "parameters": {"type": "object", "properties": {}},
            "plugin": "memory_plugin",
        },
    )

    agent.add_tool(
        "list_persistent_memory",
        list_persistent_memory,
        {
            "name": "list_persistent_memory",
            "description": "列出持久记忆区的所有条目",
            "parameters": {"type": "object", "properties": {}},
            "plugin": "memory_plugin",
        },
    )

    agent.add_tool(
        "heat_memory",
        heat_memory,
        {
            "name": "heat_memory",
            "description": "将 L2 缓存区指定索引的条目 hits +1（检索 = 访问 = 升温）",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer", "description": "L2 条目索引"}
                },
                "required": ["index"],
            },
            "plugin": "memory_plugin",
        },
    )

    agent.add_tool(
        "promote_memory",
        promote_memory,
        {
            "name": "promote_memory",
            "description": "将 L2 缓存区指定索引的条目晋升到持久记忆区（永久保存）",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer", "description": "L2 条目索引"}
                },
                "required": ["index"],
            },
            "plugin": "memory_plugin",
        },
    )

    agent.add_tool(
        "delete_from_l2",
        delete_from_l2,
        {
            "name": "delete_from_l2",
            "description": "从 L2 缓存区删除指定索引的条目",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer", "description": "L2 条目索引"}
                },
                "required": ["index"],
            },
            "plugin": "memory_plugin",
        },
    )

    agent.add_tool(
        "delete_from_persistent",
        delete_from_persistent,
        {
            "name": "delete_from_persistent",
            "description": "从持久记忆区删除指定索引的条目",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer", "description": "持久区条目索引"}
                },
                "required": ["index"],
            },
            "plugin": "memory_plugin",
        },
    )

    agent.add_tool(
        "write_persistent_memory",
        write_persistent_memory,
        {
            "name": "write_persistent_memory",
            "description": "手动写入持久记忆（由 Librarian 整理后的内容）",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "要持久化的内容"}
                },
                "required": ["content"],
            },
            "plugin": "memory_plugin",
        },
    )

    def archive_to_l2_tool(indices: list) -> str:
        """手动归档指定对话条目到 L2（秘书筛选后使用，不做语义压缩）"""
        return archive_to_l2(agent, indices)

    agent.add_tool(
        "archive_to_l2",
        archive_to_l2_tool,
        {
            "name": "archive_to_l2",
            "description": "手动归档指定对话条目到 L2 缓存（秘书筛选后使用，不做语义压缩）",
            "parameters": {
                "type": "object",
                "properties": {
                    "indices": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "要归档的对话索引列表，如 [3, 4, 5]",
                    }
                },
                "required": ["indices"],
            },
            "plugin": "memory_plugin",
        },
    )

    # 注册教训和经验本能
    def global_lessons_condition():
        return True

    def global_lessons_prompt():
        content = (
            GLOBAL_LESSONS.read_text(encoding="utf-8").strip()
            if GLOBAL_LESSONS.exists()
            else ""
        )
        if content and "暂无教训" not in content:
            return f"## 历史教训（避免重蹈覆辙）\n\n{content}"
        return ""

    def global_wins_condition():
        return True

    def global_wins_prompt():
        content = (
            GLOBAL_WINS.read_text(encoding="utf-8").strip()
            if GLOBAL_WINS.exists()
            else ""
        )
        if content and "暂无成功经验" not in content:
            return f"## 成功经验（复用有效路径）\n\n{content}"
        return ""

    def role_lessons_condition():
        return bool(agent._current_role)

    def role_lessons_prompt():
        if not agent._current_role:
            return ""
        role_lessons = ROLES_DIR / agent._current_role / "lessons.md"
        if role_lessons.exists():
            content = role_lessons.read_text(encoding="utf-8").strip()
            if content and "暂无教训" not in content:
                return f"## {agent._current_role} 专属教训\n\n{content}"
        return ""

    def role_wins_condition():
        return bool(agent._current_role)

    def role_wins_prompt():
        if not agent._current_role:
            return ""
        role_wins = ROLES_DIR / agent._current_role / "wins.md"
        if role_wins.exists():
            content = role_wins.read_text(encoding="utf-8").strip()
            if content and "暂无成功经验" not in content:
                return f"## {agent._current_role} 专属成功经验\n\n{content}"
        return ""

    agent.instinct_registry.register(
        "global_lessons", global_lessons_condition, global_lessons_prompt
    )
    agent.instinct_registry.register(
        "global_wins", global_wins_condition, global_wins_prompt
    )
    agent.instinct_registry.register(
        "role_lessons", role_lessons_condition, role_lessons_prompt
    )
    agent.instinct_registry.register("role_wins", role_wins_condition, role_wins_prompt)

    return {
        "name": "memory_plugin",
        "version": "3.1.0",
        "author": "AgentCore",
        "description": "本体记忆 — L2缓存区(本能管理) + 持久区(Librarian管理)",
        "tools": [
            "read_global_memory",
            "write_global_memory",
            "append_global_memory",
            "archive_to_l2",
            "list_l2_cache",
            "list_persistent_memory",
            "heat_memory",
            "promote_memory",
            "delete_from_l2",
            "delete_from_persistent",
            "write_persistent_memory",
        ],
    }
