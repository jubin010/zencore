#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MiniMax + Ollama 双模型工具调用测试
"""

import sys
from pathlib import Path

AGENT_CORE_DIR = Path(__file__).parent
sys.path.insert(0, str(AGENT_CORE_DIR))

from core.agent import AgentCore
from drivers.cli_driver import CLIDriver

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


def run_tests(model_config, label):
    global passed, failed
    print(f"\n{'=' * 60}")
    print(f"🧪 测试 {label}")
    print(f"{'=' * 60}")

    driver = CLIDriver(model_config=model_config)
    agent = AgentCore(driver=driver)
    agent.clear_history()
    agent._consecutive_failures = 0

    # 测试 1: 单轮工具调用
    print(f"\n📝 1. 单轮工具调用 — get_cwd")
    resp = agent.chat_with_tools("用 get_cwd 查看当前目录")
    print(f"  响应: {resp[:100]}")
    test("get_cwd 调用成功", "zencore" in resp or "my_github" in resp, resp[:80])
    test(
        "历史消息数 >= 4",
        len(agent.conversation_history) >= 4,
        f"实际: {len(agent.conversation_history)}",
    )

    # 测试 2: 第二轮工具调用
    print(f"\n📝 2. 第二轮工具调用 — list_files")
    resp = agent.chat_with_tools("用 list_files 列出当前目录")
    print(f"  响应: {resp[:100]}")
    test(
        "list_files 调用成功",
        len(agent.conversation_history) >= 8,
        f"实际: {len(agent.conversation_history)}",
    )

    # 测试 3: 带参数的工具调用
    print(f"\n📝 3. 带参数工具调用 — run_command")
    resp = agent.chat_with_tools("用 run_command 执行 'echo hello_test'")
    print(f"  响应: {resp[:100]}")
    test("run_command 调用成功", "hello_test" in resp, resp[:80])

    # 测试 4: 纯文字回复
    print(f"\n📝 4. 纯文字回复")
    resp = agent.chat_with_tools("你好，简单回复")
    print(f"  响应: {resp[:100]}")
    test("纯文字回复正常", len(resp) > 5, resp[:50])

    # 验证消息格式
    print(f"\n📋 消息格式验证:")
    tool_msgs = [m for m in agent.conversation_history if m.get("role") == "tool"]
    assistant_tc = [
        m
        for m in agent.conversation_history
        if m.get("role") == "assistant" and m.get("tool_calls")
    ]
    print(f"  assistant tool_calls 消息数: {len(assistant_tc)}")
    print(f"  tool 消息数: {len(tool_msgs)}")
    test(
        "tool_call_id 匹配",
        len(tool_msgs) == len(assistant_tc),
        f"tool={len(tool_msgs)}, assistant_tc={len(assistant_tc)}",
    )


# MiniMax
run_tests(
    {
        "name": "MiniMax M2.7",
        "host": "https://api.minimaxi.com/v1",
        "model": "MiniMax-M2.7",
        "api_key": "sk-cp-wx_UElOKRzcYkh2zuTlkJod-VclfSE0RE9AJdPpgxP-_7HQJREEjR4b6WMq-hLcXCJPMXoKdZhcqg-8G50R-V2iIoTivLoR1QgCAmh9W2Vg1nqsrO7d0OO0",
        "thinking": False,
    },
    "MiniMax M2.7",
)

# Ollama
run_tests(
    {
        "name": "本地 Qwen3.5",
        "host": "http://192.168.1.24:11434",
        "model": "qwen3.5:9b",
        "api_key": "ollama",
        "thinking": False,
    },
    "Ollama (qwen3.5:9b)",
)

print(f"\n{'=' * 60}")
print(f"📊 总计: {passed} 通过, {failed} 失败")
print(f"{'=' * 60}")
if failed == 0:
    print("🎉 全部通过!")
else:
    print(f"⚠️ 有 {failed} 个测试失败")
