"""
summarize_plugin - 上下文摘要插件
功能：当上下文过长时，调用 LLM 摘要历史对话
"""

from pathlib import Path

AGENT_ROOT = Path(__file__).parent.parent.parent


def register(agent):
    """注册摘要插件"""

    def summarize_context(max_items: int = 10) -> str:
        """摘要上下文

        将较早的对话历史提交给 LLM 摘要，保留近期全量对话。
        这是处理上下文膨胀的机制，不是工具调用。

        Args:
            max_items: 保留最近 N 条对话全量，之前的进行摘要
        """
        history = agent.conversation_history
        if len(history) <= max_items:
            return f"上下文共 {len(history)} 条，无需摘要"

        # 分离需要摘要的和需要保留的
        to_summarize = history[:-max_items]
        to_keep = history[-max_items:]

        # 构建摘要 prompt
        summary_lines = []
        for msg in to_summarize:
            role = msg.get("role", "")
            content = msg.get("content", "") or ""

            if role == "tool":
                name = msg.get("name", "unknown")
                summary_lines.append(f"[tool] {name}: {content[:100]}...")
            elif role == "assistant" and msg.get("tool_calls"):
                tcs = msg.get("tool_calls", [])
                tc_names = ", ".join([tc.get("function", {}).get("name", "?") for tc in tcs])
                summary_lines.append(f"[assistant] 调用工具: {tc_names}")
            elif content:
                # 截断过长内容
                if len(content) > 200:
                    content = content[:200] + "..."
                summary_lines.append(f"[{role}] {content}")

        history_text = "\n".join(summary_lines)

        summarize_prompt = f"""## 任务：摘要上下文

请将以下对话历史压缩为简洁的摘要，保留关键信息：

---
{history_text}
---

摘要要求：
1. 保留用户的主要需求/问题
2. 保留 AI 执行的关键操作和结果
3. 压缩重复/冗余内容
4. 返回格式：[摘要] 关键结论 + [详情] 具体摘要

请直接返回摘要，不要有多余的解释。"""

        # 直接调用 driver LLM，不走 chat_with_tools 循环
        messages = [{"role": "user", "content": summarize_prompt}]
        try:
            result = agent.driver.call_llm(messages)
            summary = result.get("content", "")

            if not summary:
                return "摘要失败：LLM 未返回内容"

            # 创建摘要消息
            summary_msg = {
                "role": "system",
                "content": f"[上下文摘要]\n{summary}\n[/上下文摘要]"
            }

            # 替换历史：摘要 + 保留的对话
            agent.conversation_history = [summary_msg] + to_keep

            # 立即保存
            agent.save_history()

            original_count = len(history)
            new_count = len(agent.conversation_history)
            return f"✅ 上下文摘要完成：{original_count} 条 → {new_count} 条\n{summary[:200]}..."

        except Exception as e:
            return f"❌ 摘要失败: {e}"

    agent.add_tool(
        "summarize_context",
        summarize_context,
        {
            "name": "summarize_context",
            "description": "当上下文过长时，调用此工具摘要历史对话。保留近期对话，压缩早期对话为摘要。",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_items": {
                        "type": "integer",
                        "description": "保留最近 N 条对话全量，默认 10"
                    }
                }
            },
            "plugin": "summarize_plugin",
        },
    )

    return {
        "name": "summarize_plugin",
        "version": "1.0.0",
        "author": "AgentCore",
        "description": "上下文摘要 - 处理上下文膨胀，自动摘要历史对话",
        "tools": ["summarize_context"],
    }