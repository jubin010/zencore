#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 MiniMax M2.7 多轮工具调用（使用原生 tool_calls）
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

print("=" * 60)
print("🧪 测试 MiniMax M2.7 多轮工具调用（原生 tool_calls）")
print("=" * 60)

# 测试 1：单轮工具调用
print("\n📝 测试 1：单轮工具调用 — 查询当前目录")
print("-" * 40)
response = agent.chat_with_tools("用 get_cwd 查看当前工作目录")
print(f"✅ 响应: {response[:200]}")
print(f"   历史消息数: {len(agent.conversation_history)}")

print("\n📋 历史消息格式:")
for i, msg in enumerate(agent.conversation_history):
    role = msg.get("role", "?")
    has_tool_calls = "tool_calls" in msg
    has_tool_call_id = "tool_call_id" in msg
    content_preview = str(msg.get("content", ""))[:80]
    print(
        f"  [{i}] role={role}, tool_calls={has_tool_calls}, tool_call_id={has_tool_call_id}, content={content_preview}"
    )

# 测试 2：多轮工具调用
print("\n\n📝 测试 2：多轮工具调用 — 列出当前目录文件")
print("-" * 40)
response = agent.chat_with_tools("现在列出当前目录下的文件")
print(f"✅ 响应: {response[:300]}")
print(f"   历史消息数: {len(agent.conversation_history)}")

print("\n📋 完整历史消息格式:")
for i, msg in enumerate(agent.conversation_history):
    role = msg.get("role", "?")
    has_tool_calls = "tool_calls" in msg
    has_tool_call_id = "tool_call_id" in msg
    content_preview = str(msg.get("content", ""))[:80]
    print(
        f"  [{i}] role={role}, tool_calls={has_tool_calls}, tool_call_id={has_tool_call_id}, content={content_preview}"
    )

# 测试 3：连续多轮工具调用
print("\n\n📝 测试 3：连续工具调用 — 执行一个命令")
print("-" * 40)
response = agent.chat_with_tools("用 run_command 执行 'echo hello world' 命令")
print(f"✅ 响应: {response[:300]}")
print(f"   历史消息数: {len(agent.conversation_history)}")

# 测试 4：纯文字回复
print("\n\n📝 测试 4：纯文字回复")
print("-" * 40)
response = agent.chat_with_tools("你好，请简单介绍一下自己")
print(f"✅ 响应: {response[:200]}")
print(f"   历史消息数: {len(agent.conversation_history)}")

print("\n" + "=" * 60)
print("✅ 所有测试完成!")
print("=" * 60)
