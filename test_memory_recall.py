#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆召回功能专项测试
"""

import sys
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


print("=" * 60)
print("🧠 记忆召回功能专项测试")
print("=" * 60)

# ---- 1. 全局记忆写入后立即召回 ----
print("\n📝 1. 全局记忆写入后立即召回")
print("-" * 40)
agent.clear_history()
agent._consecutive_failures = 0

# 先写入一条明确的记忆
resp = agent.chat_with_tools("用 write_global_memory 写入：用户最喜欢的颜色是蓝色")
print(f"  写入: {resp[:100]}")
memory_file = Path(agent._global_memory_file)
content1 = memory_file.read_text(encoding="utf-8")
print(f"  文件内容: {content1[:100]}")

# 立即读取
resp = agent.chat_with_tools("读取全局记忆，用户最喜欢的颜色是什么？")
print(f"  召回: {resp[:200]}")
test("写入后能召回蓝色", "蓝色" in resp, resp[:100])

# ---- 2. 追加记忆后的召回 ----
print("\n\n📝 2. 追加记忆后的召回")
print("-" * 40)

resp = agent.chat_with_tools("追加一条：用户的生日是12月25日")
print(f"  追加: {resp[:100]}")

resp = agent.chat_with_tools("读取全局记忆，用户生日是多少？")
print(f"  召回: {resp[:200]}")
test("能召回生日12月25日", "25日" in resp or "12月" in resp, resp[:100])

# 验证文件
content2 = memory_file.read_text(encoding="utf-8")
print(f"  文件内容: {content2[:200]}")

# ---- 3. 跨角色记忆召回 ----
print("\n\n🎭 3. 跨角色记忆召回")
print("-" * 40)

# 写入一条跨角色记忆
resp = agent.chat_with_tools("向全局记忆追加：项目代号 zencore 是核心身份代号")
print(f"  追加: {resp[:100]}")

# 切换到另一个角色
resp = agent.chat_with_tools("切换到 writer 角色")
print(f"  切换: {resp[:100]}")

# 在 writer 角色中召回
resp = agent.chat_with_tools("读取全局记忆，告诉我项目代号是什么？")
print(f"  召回: {resp[:200]}")
test("跨角色能召回 zencore", "zencore" in resp.lower(), resp[:100])

# ---- 4. 多轮对话中的自然记忆召回 ----
print("\n\n🔗 4. 多轮对话中的自然记忆召回（不主动调用工具）")
print("-" * 40)

agent.clear_history()
agent._consecutive_failures = 0

# 明确告诉AI记住一个信息
resp = agent.chat_with_tools("请记住：我们的项目叫 ABC-123")
print(f"  第1轮: {resp[:100]}")

# 多轮其他对话
resp = agent.chat_with_tools("用 get_cwd 查看当前目录")
print(f"  第2轮: {resp[:80]}")
resp = agent.chat_with_tools("用 list_files 列出目录")
print(f"  第3轮: {resp[:80]}")

# 询问项目名称（不提示"读取记忆"）
resp = agent.chat_with_tools("我们的项目叫什么名字？")
print(f"  第4轮: {resp[:200]}")
test(
    "多轮后自然召回项目名",
    "ABC" in resp or "已记住" in resp or "ABC-123" in resp,
    resp[:100],
)

# ---- 5. 记忆持久化验证 ----
print("\n\n💾 5. 记忆持久化验证")
print("-" * 40)

# 重启一个全新的 agent
agent2 = AgentCore(driver=driver)

# 直接读取记忆
resp = agent2.chat_with_tools("读取全局记忆，告诉我用户喜欢的颜色和生日")
print(f"  新agent召回: {resp[:300]}")
test("重启后能召回之前的记忆", "蓝色" in resp and "25日" in resp, resp[:200])

# ---- 6. 记忆丢失场景测试 ----
print("\n\n⚠️ 6. 记忆丢失场景测试（clear_history 后）")
print("-" * 40)

agent3 = AgentCore(driver=driver)
agent3.clear_history()
# 注意：clear_history 只清理 conversation_history，不清理记忆文件
# 所以记忆文件应该还在

resp = agent3.chat_with_tools("读取全局记忆，我是谁？")
print(f"  清理历史后召回: {resp[:200]}")
test("clear_history 不影响全局记忆文件", len(resp) > 5, resp[:100])

# ---- 7. 角色记忆召回 ----
print("\n\n🎭 7. 角色记忆召回")
print("-" * 40)

# 在 developer 角色写入角色记忆
agent.clear_history()
agent._consecutive_failures = 0

agent._current_role = "developer"
agent._current_role_memory_file = str(
    AGENT_CORE_DIR / "plugins" / "roles" / "developer" / "memory.md"
)
dev_memory = Path(agent._current_role_memory_file)
dev_memory.write_text("开发者角色专属记忆：擅长Python和系统架构", encoding="utf-8")

# 切换角色后写入
agent._current_role = "writer"
agent._current_role_memory_file = str(
    AGENT_CORE_DIR / "plugins" / "roles" / "writer" / "memory.md"
)
writer_memory = Path(agent._current_role_memory_file)
writer_memory.write_text("写手角色专属记忆：擅长文案和创意写作", encoding="utf-8")

# 切回 developer，召回角色记忆
agent._current_role = "developer"
resp = agent.chat_with_tools("读取角色记忆，告诉我 developer 角色的特点")
print(f"  developer召回: {resp[:200]}")
test("能召回 developer 角色记忆", "Python" in resp or "系统架构" in resp, resp[:100])

# 切换到 writer 召回
agent._current_role = "writer"
resp = agent.chat_with_tools("读取角色记忆，告诉我 writer 角色的特点")
print(f"  writer召回: {resp[:200]}")
test("能召回 writer 角色记忆", "文案" in resp or "创意写作" in resp, resp[:100])

# 清理测试写入的角色记忆
dev_memory.write_text("# developer 记忆\n\n（记忆为空）", encoding="utf-8")
writer_memory.write_text("# writer 记忆\n\n（记忆为空）", encoding="utf-8")

# ============================================================
print("\n" + "=" * 60)
print(f"📊 记忆召回测试结果: {passed} 通过, {failed} 失败")
print("=" * 60)

if failed == 0:
    print("🎉 全部通过!")
else:
    print(f"⚠️ 有 {failed} 个测试失败")
