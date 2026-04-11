#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zencore 全核心功能测试 + 记忆功能测试
"""

import sys
import json
from pathlib import Path

AGENT_CORE_DIR = Path(__file__).parent
sys.path.insert(0, str(AGENT_CORE_DIR))

from core.agent import AgentCore
from drivers.cli_driver import CLIDriver

model_config = {
    "name": "MiniMax M2.7",
    "host": "https://api.minimaxi.com/v1",
    "model": "MiniMax-M2.7",
    "api_key": "sk-cp-wx_UElOKRzcYkh2zuTlkJod-VclfSE0RE9AJdPpgxP-_7HQJREEjR4b6WMq-hLcXCJPMXoKdZhcqg-8G50R-V2iIoTivLoR1QgCAmh9W2Vg1nqsrO7d0OO0",
    "thinking": False,
}

driver = CLIDriver(model_config=model_config)
agent = AgentCore(driver=driver)

passed = 0
failed = 0


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} — {detail}")


# ============================================================
print("=" * 60)
print("🧪 zencore 全核心功能测试")
print("=" * 60)

# ---- 1. 插件加载 ----
print("\n📦 1. 核心插件加载")
tools = agent.list_tools()
test("plugin_builder 已加载", any("write_plugin" in t for t in tools))
test("env_plugin 已加载", any("get_cwd" in t for t in tools))
test("memory_plugin 已加载", any("read_global_memory" in t for t in tools))
test("watcher_plugin 已加载", any("scan_plugins" in t for t in tools))
test("role_plugin 已加载", any("list_roles" in t for t in tools))
test("instinct_plugin 已加载", len(agent.instinct_registry._instincts) == 3)

# ---- 2. 工具数量 ----
print("\n🛠️ 2. 工具数量")
print(f"   总工具数: {len(tools)}")
test("工具数 >= 20", len(tools) >= 20, f"实际: {len(tools)}")

# ---- 3. 本能系统 ----
print("\n🧬 3. 本能系统")
test(
    "拥挤本能已注册",
    any(i["name"] == "crowding" for i in agent.instinct_registry._instincts),
)
test(
    "微扰本能已注册",
    any(i["name"] == "mild" for i in agent.instinct_registry._instincts),
)
test(
    "挫败本能已注册",
    any(i["name"] == "frustration" for i in agent.instinct_registry._instincts),
)

# 拥挤本能条件测试
agent.conversation_history = [{"role": "user", "content": "x"}] * 41
test("拥挤本能触发 (>40条)", agent.instinct_registry._instincts[0]["condition"]())
agent.conversation_history = agent.conversation_history[:5]
test("拥挤本能不触发 (<40条)", not agent.instinct_registry._instincts[0]["condition"]())

# 挫败本能条件测试
agent._consecutive_failures = 0
test(
    "挫败本能不触发 (0次失败)", not agent.instinct_registry._instincts[2]["condition"]()
)
agent._consecutive_failures = 2
test("挫败本能触发 (2次失败)", agent.instinct_registry._instincts[2]["condition"]())
agent._consecutive_failures = 0

# ---- 4. 工具执行 ----
print("\n⚙️ 4. 工具执行")
result = agent.execute_tool("get_cwd")
test("get_cwd 执行成功", "/home/jubin/my_github/zencore" in result, result)

result = agent.execute_tool("list_files")
test("list_files 执行成功", ".git" in result or "core" in result, result[:100])

result = agent.execute_tool("run_command", command="echo test123")
test("run_command 执行成功", "test123" in result, result)

result = agent.execute_tool("nonexistent_tool")
test("未知工具返回错误", "❌" in result)

# ---- 5. 消息格式 ----
print("\n📨 5. 消息格式")
agent.clear_history()
agent.add_message("user", "hello")
test(
    "user 消息格式正确",
    agent.conversation_history[-1] == {"role": "user", "content": "hello"},
)

agent.add_message(
    "assistant",
    content="",
    tool_calls=[
        {
            "id": "tc1",
            "type": "function",
            "function": {"name": "get_cwd", "arguments": "{}"},
        }
    ],
)
test("assistant tool_calls 格式正确", "tool_calls" in agent.conversation_history[-1])
test("assistant content 为空字符串", agent.conversation_history[-1]["content"] == "")

agent.add_message("tool", content="result", tool_call_id="tc1")
test("tool tool_call_id 匹配", agent.conversation_history[-1]["tool_call_id"] == "tc1")

# ---- 6. 历史截断 ----
print("\n📏 6. 历史截断")
agent.clear_history()
for i in range(60):
    agent.add_message("user", f"msg_{i}")
test(
    "历史截断到 max_history",
    len(agent.conversation_history) <= agent.max_history,
    f"实际: {len(agent.conversation_history)}",
)

# ============================================================
print("\n" + "=" * 60)
print("🧠 记忆功能测试")
print("=" * 60)

# 清理历史，开始记忆测试
agent.clear_history()
agent._consecutive_failures = 0

# ---- 7. 写入全局记忆 ----
print("\n📝 7. 写入全局记忆")
resp = agent.chat_with_tools(
    "用 write_global_memory 写入：项目代号是 zencore，核心理念是一切皆为插件"
)
print(f"   响应: {resp[:150]}")
# 检查记忆文件
memory_file = Path(agent._global_memory_file)
test("全局记忆文件存在", memory_file.exists())
if memory_file.exists():
    content = memory_file.read_text(encoding="utf-8")
    test("记忆内容包含 zencore", "zencore" in content.lower(), content[:100])
    test("记忆内容包含 一切皆为插件", "一切皆为插件" in content, content[:100])

# ---- 8. 读取全局记忆 ----
print("\n📖 8. 读取全局记忆")
resp = agent.chat_with_tools("用 read_global_memory 读取全局记忆")
print(f"   响应: {resp[:200]}")
test("读取响应包含 zencore", "zencore" in resp.lower() or "插件" in resp, resp[:100])

# ---- 9. 追加全局记忆 ----
print("\n➕ 9. 追加全局记忆")
resp = agent.chat_with_tools(
    "用 append_global_memory 追加一条：当前测试时间是 2026年4月"
)
print(f"   响应: {resp[:150]}")
if memory_file.exists():
    content = memory_file.read_text(encoding="utf-8")
    test("记忆内容包含 2026年4月", "2026年4月" in content, content[-200:])

# ---- 10. 角色记忆 ----
print("\n🎭 10. 角色记忆")
resp = agent.chat_with_tools("切换到 developer 角色")
print(f"   响应: {resp[:200]}")
test(
    "当前角色是 developer",
    agent._current_role == "developer",
    f"实际: {agent._current_role}",
)
test(
    "角色记忆文件已设置",
    agent._current_role_memory_file != "",
    agent._current_role_memory_file,
)

# 检查 developer 角色记忆文件
dev_memory = Path(agent._current_role_memory_file)
test("developer 记忆文件存在", dev_memory.exists())

# ---- 11. 角色切换后记忆隔离 ----
print("\n🔄 11. 角色切换记忆隔离")
resp = agent.chat_with_tools("切换到 writer 角色")
print(f"   响应: {resp[:150]}")
test(
    "当前角色是 writer", agent._current_role == "writer", f"实际: {agent._current_role}"
)
writer_memory = Path(agent._current_role_memory_file)
test("writer 记忆文件不同", str(writer_memory) != str(dev_memory))

# 切回 developer
resp = agent.chat_with_tools("切换回 developer 角色")
test(
    "切回 developer", agent._current_role == "developer", f"实际: {agent._current_role}"
)
test("记忆文件恢复为 developer", str(dev_memory) == agent._current_role_memory_file)

# ---- 12. 记忆在对话中的注入 ----
print("\n💉 12. 记忆在 System Prompt 中的注入")
prompt = agent._build_prompt("")
messages = json.loads(prompt)
system_content = messages[0]["content"]
test("System Prompt 包含全局记忆路径", agent._global_memory_file in system_content)
test(
    "System Prompt 包含角色记忆路径", agent._current_role_memory_file in system_content
)
test("System Prompt 包含当前角色", "developer" in system_content)

# ---- 13. 多轮对话 + 记忆连贯性 ----
print("\n🔗 13. 多轮对话记忆连贯性")
agent.clear_history()

# 第一轮：写入记忆
resp1 = agent.chat_with_tools("记住这个密码：admin123")
print(f"   第1轮: {resp1[:100]}")

# 第二轮：查询记忆
resp2 = agent.chat_with_tools("读取全局记忆，告诉我你记住了什么")
print(f"   第2轮: {resp2[:200]}")
test("第二轮能访问到记忆", len(resp2) > 10, resp2[:100])

# ---- 14. 教训加载 ----
print("\n📚 14. 教训加载")
lessons = agent._load_lessons("developer")
test("教训加载返回内容", len(lessons) > 0)
print(f"   教训内容: {lessons[:100]}...")

# ---- 15. 插件动态加载/卸载 ----
print("\n🔌 15. 插件动态加载")
# 核心插件始终已加载，_loaded_plugins 仅跟踪动态加载的非核心插件
test("核心插件工具总数正确", len(tools) == 24, f"实际: {len(tools)}")

# ============================================================
print("\n" + "=" * 60)
print(f"📊 测试结果: {passed} 通过, {failed} 失败")
print("=" * 60)

if failed == 0:
    print("🎉 全部测试通过!")
else:
    print(f"⚠️ 有 {failed} 个测试失败，请检查上方输出")
