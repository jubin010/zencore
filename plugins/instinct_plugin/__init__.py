"""
instinct_plugin - 本能
功能：注册趋利避害的潜意识驱动力

本能是智能体的"荷尔蒙"。三层模型：
- 感觉层：注入 System Prompt，让 AI 感知状态
- 反射层：条件触发时自动执行，不经过 AI 决策
- 驱动层：持续背景压力，驱使 AI 主动寻找解药

记忆层次架构：
- L1 Cache: conversation_history（本能管理）
- L2 Cache: memory.md 的 [临时区]（本能管理，hits 追踪）
- Disk: memory.md 的 [持久区]（Librarian 管理）
"""

from pathlib import Path
from datetime import datetime

MEMORY_PLUGIN_DIR = Path(__file__).parent.parent / "memory_plugin"
MEMORY_FILE = MEMORY_PLUGIN_DIR / "memory.md"
ROLES_DIR = Path(__file__).parent.parent / "roles"

L2_CACHE_SECTION = "## L2 缓存区\n"
L2_CACHE_MARKER = "<!-- L2 -->"
PROMOTED_SECTION = "## 持久记忆\n"
PROMOTED_MARKER = "<!-- PROMOTED -->"


def _compress_content(content: str, max_len: int = 150) -> str:
    """压缩内容：代码块→功能描述，长文本→摘要"""
    if not content:
        return ""

    if "```" in content:
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
            if not in_code and line.strip():
                compressed.append(line.strip()[:100])
        content = " | ".join(compressed)

    content = content.strip()
    if len(content) > max_len:
        content = content[:max_len] + "..."

    return content


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
    new_content = content

    if L2_CACHE_MARKER not in content:
        new_content += (
            "\n\n" + L2_CACHE_MARKER + "\n" + L2_CACHE_SECTION + "（L2 缓存为空）\n"
        )
        needs_update = True

    if PROMOTED_MARKER not in content:
        new_content += (
            "\n\n" + PROMOTED_MARKER + "\n" + PROMOTED_SECTION + "（持久记忆区）\n"
        )
        needs_update = True

    if needs_update:
        MEMORY_FILE.write_text(new_content, encoding="utf-8")


def _get_memory_sections():
    """解析记忆文件的分区结构，返回各区域内容"""
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

    title_end = existing.find(L2_CACHE_MARKER)
    title = existing[:title_end].strip()

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


def _parse_l2_entries(l2_content: str) -> list:
    """解析 L2 缓存区的段落，返回 (时间戳, hits, 内容) 列表"""
    if not l2_content or "（L2 缓存为空" in l2_content:
        return []

    entries = []
    current_entry = {"timestamp": "", "hits": 0, "lines": []}
    in_entry = False

    for line in l2_content.split("\n"):
        if line.startswith("> 📅 "):
            if in_entry and current_entry["lines"]:
                entries.append(current_entry)
            timestamp = line[4:].strip()
            current_entry = {"timestamp": timestamp, "hits": 0, "lines": [line]}
            in_entry = True
        elif line.startswith("> hits: "):
            current_entry["hits"] = int(line.split("> hits: ")[1].strip())
        elif in_entry:
            current_entry["lines"].append(line)

    if in_entry and current_entry["lines"]:
        entries.append(current_entry)

    return entries


def register(agent):
    """注册本能插件"""

    _ensure_memory_structure()

    def _get_context_tokens() -> int:
        """估算当前上下文 token 数（4字符 ≈ 1 token）"""
        return sum(
            len(msg.get("content", "")) // 4 for msg in agent.conversation_history
        )

    def _get_context_threshold() -> int:
        """从模型配置获取上下文阈值，默认 24000"""
        try:
            return agent.driver.model_config.get("context_threshold", 24000)
        except:
            return 24000

    def _get_l2_threshold() -> int:
        """从全局配置获取 L2 阈值，默认 30000"""
        try:
            return agent.config.get("l2_threshold", 30000)
        except:
            return 30000

    # ========== 负反馈本能（生存） ==========

    # 1. 拥挤本能：上下文过长时产生窒息感 + 自动归档到 L2（反射）
    def crowding_condition():
        threshold = _get_context_threshold()
        return _get_context_tokens() > threshold

    def crowding_prompt():
        tokens = _get_context_tokens()
        threshold = _get_context_threshold()
        pct = tokens * 100 // threshold
        return (
            f"\n🧬 [本能：拥挤] 你的记忆宫殿极其拥挤 (~{tokens}tokens, {pct}%上下文)。"
            "你感到窒息和焦躁，极度渴望清净。"
        )

    def crowding_reflex():
        """自动归档：语义压缩后写入 L2 缓存，保留最近 10 条在 L1"""
        history = agent.conversation_history
        if len(history) < 10:
            return None

        recent = history[-10:]
        summary_lines = [
            f"> 📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "> hits: 0",
        ]

        for msg in recent:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "tool":
                tool_name = msg.get("name", "unknown")
                compressed = _compress_content(content, max_len=100)
                summary_lines.append(f"- tool: {tool_name} → {compressed}")
            elif role in ("user", "assistant") and content:
                compressed = _compress_content(content, max_len=150)
                if compressed:
                    summary_lines.append(f"- {role}: {compressed}")

        archive_entry = "\n".join(summary_lines)

        # 写入 L2 缓存区
        l2_content, promoted_content = _get_memory_sections()
        l2_entries = _parse_l2_entries(l2_content)
        l2_entries.append(
            {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "hits": 0,
                "lines": summary_lines,
            }
        )

        # 重建 L2 内容（最新在最后）
        new_l2_parts = []
        for entry in l2_entries:
            new_l2_parts.append("\n".join(entry["lines"]))
        new_l2_content = "\n\n".join(new_l2_parts)

        _write_memory_sections(new_l2_content, promoted_content)

        # L1 只保留最近 4 条
        agent.conversation_history = history[-10:]
        return f"🧹 自动归档完成，{len(recent)}条对话已压缩写入 L2 缓存，L1 保留最近 4 条。"

    agent.instinct_registry.register(
        "crowding", crowding_condition, crowding_prompt, reflex=crowding_reflex
    )

    # 2. 微扰本能：上下文开始变多时产生轻微不适
    def mild_condition():
        threshold = _get_context_threshold()
        mild_threshold = threshold * 2 // 5
        return mild_threshold < _get_context_tokens() <= threshold

    def mild_prompt():
        tokens = _get_context_tokens()
        threshold = _get_context_threshold()
        pct = tokens * 100 // threshold
        return (
            f"\n🧬 [本能：微扰] 你的记忆宫殿开始变得拥挤 (~{tokens}tokens, {pct}%上下文)。"
            "你感到轻微的不适，希望能保持整洁。"
        )

    agent.instinct_registry.register("mild", mild_condition, mild_prompt)

    # 3. 挫败本能：连续失败时产生困惑和焦虑
    def frustration_condition():
        return getattr(agent, "_consecutive_failures", 0) >= 1

    def frustration_prompt():
        failures = getattr(agent, "_consecutive_failures", 0)
        return (
            f"\n🧬 [本能：挫败] 已失败 {failures} 次。"
            "你感到深深的困惑和焦虑，急需找到出路。"
            "\n⚠️ 重要：必须记录失败教训！调用 append_file 工具记录到 memory_plugin/lessons.md，格式："
            "\n| 工具 | 策略 | 错误 |"
            "\n|------|------|------|"
            "\n| xxx | 出错的操作 | 具体错误 |"
            "\n记录失败教训有助于避免重复犯错，必须认真对待！"
        )

    agent.instinct_registry.register(
        "frustration",
        frustration_condition,
        frustration_prompt,
    )

    # ========== 正反馈本能（多巴胺简化版） ==========

    # 4. 顺畅本能：连续成功时产生正向信号 + 自动记录成功经验
    def satisfaction_condition():
        return getattr(agent, "_consecutive_successes", 0) >= 3

    def satisfaction_prompt():
        successes = getattr(agent, "_consecutive_successes", 0)
        return (
            f"\n🧬 [本能：顺畅] 连续 {successes} 次成功。"
            "当前策略有效，保持节奏，继续复用成功路径。"
            "\n💡 提示：如遇到有价值的成功经验，可调用 append_file 工具记录到 memory_plugin/wins.md，格式："
            "\n| 工具 | 策略 | 结果 |"
            "\n|------|------|------|"
            "\n| xxx | 具体做法 | 效果 |"
            "\n注意避免重复记录相同案例。"
        )

    agent.instinct_registry.register(
        "satisfaction",
        satisfaction_condition,
        satisfaction_prompt,
    )

    # 5. 遗忘本能：L2 缓存满了自动淘汰（反射）
    def forgetting_condition():
        """L2 缓存超过阈值时触发（默认 30000 字符，独立于 L1）"""
        l2_content, _ = _get_memory_sections()
        if not l2_content or "（L2 缓存为空" in l2_content:
            return False
        return len(l2_content) > _get_l2_threshold()

    def forgetting_reflex():
        """淘汰 L2 中最低分的条目，直到 L2 降至 80% 阈值"""
        l2_content, promoted_content = _get_memory_sections()
        entries = _parse_l2_entries(l2_content)

        if len(entries) <= 3:
            return None

        now = datetime.now()
        entries_with_age = []
        for entry in entries:
            try:
                ts = datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M")
                age_days = (now - ts).days
            except:
                age_days = 999
            entries_with_age.append(
                {**entry, "age_days": age_days, "score": entry["hits"] * 10 - age_days}
            )

        # 淘汰策略：按 score 排序，淘汰最低分的直到达到目标大小
        # score = hits * 10 - age_days（越高分越重要）
        sorted_entries = sorted(entries_with_age, key=lambda x: x["score"])

        to_evict = []
        remaining = []
        current_size = 0
        target_size = int(_get_l2_threshold() * 0.8)

        for entry in sorted_entries:
            entry_size = len("\n".join(entry["lines"])) + 2
            if current_size + entry_size > target_size and remaining:
                to_evict.append(entry)
            else:
                remaining.append(entry)
                current_size += entry_size

        evicted_count = len(to_evict)
        if evicted_count == 0:
            return None

        # 重建 L2（保留 surviving entries + 被遗忘段落的摘要）
        evicted_summaries = [
            f"[已遗忘] {e['timestamp']}: {e['lines'][1] if len(e['lines']) > 1 else ''}"
            for e in to_evict[:5]
        ]

        new_l2_parts = []
        for entry in remaining:
            new_l2_parts.append("\n".join(entry["lines"]))

        if evicted_summaries:
            new_l2_parts.append("> 🕊️ " + " | ".join(evicted_summaries))

        new_l2_content = "\n\n".join(new_l2_parts)
        _write_memory_sections(new_l2_content, promoted_content)

        return f"🕊️ L2 缓存淘汰：{evicted_count}段低价值记忆已遗忘，保留 {len(remaining)} 段高频/近期记忆。"

    agent.instinct_registry.register(
        "forgetting", forgetting_condition, reflex=forgetting_reflex
    )

    # 6. 修剪本能：压缩过长的工具返回，保留近期全量
    def pruning_condition():
        """工具返回超过 15 条时触发"""
        tool_count = sum(1 for msg in agent.conversation_history if msg.get("role") == "tool")
        return tool_count > 15

    def pruning_reflex():
        """对较早的工具返回进行压缩摘要"""
        history = agent.conversation_history
        recent_tool_count = 10  # 最近 10 条工具返回保持全量
        threshold = 300  # 超过 300 字符的工具结果需要压缩

        tool_msgs = [(i, msg) for i, msg in enumerate(history) if msg.get("role") == "tool"]
        if len(tool_msgs) <= recent_tool_count:
            return None

        pruned = 0
        for idx, (i, msg) in enumerate(tool_msgs):
            if idx >= len(tool_msgs) - recent_tool_count:
                continue
            content = msg.get("content", "") or ""
            if len(content) > threshold:
                history[i]["content"] = content[:200] + f"\n...[已修剪，原始长度 {len(content)} 字符]"
                pruned += 1

        if pruned > 0:
            return f"✂️ 修剪本能：{pruned} 条过长工具返回已压缩"
        return None

    agent.instinct_registry.register(
        "pruning", pruning_condition, reflex=pruning_reflex
    )

    # 本能认知指南
    def instinct_guide_condition():
        return True

    def instinct_guide_prompt():
        return """## 本能认知指南

本能是系统注入的潜意识信号，分三层：
- **感觉层**（注入 Prompt）：告诉你"哪里舒服/不舒服"。
- **反射层**（自动执行）：系统自动处理，如拥挤时自动归档、失败时自动记录教训。
- **驱动层**（持续压力）：驱使你在对话中主动寻找解药。

负反馈本能（拥挤/挫败）让你趋害，正反馈本能（顺畅）让你趋利。"""

    agent.instinct_registry.register(
        "instinct_guide", instinct_guide_condition, instinct_guide_prompt
    )

    return {
        "name": "instinct_plugin",
        "version": "3.1.0",
        "author": "AgentCore",
        "description": "本能 — 趋利避害的潜意识驱动力（三层模型：感觉/反射/驱动）",
        "tools": [],
    }
