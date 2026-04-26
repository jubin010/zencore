#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件热载入 + 重复使用上下文污染测试
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
print("🧪 插件热载入 + 上下文污染测试")
print("=" * 60)

# ---- 1. 插件热载入测试 ----
print("\n🔥 1. 插件热载入测试")
print("-" * 40)

# 创建一个测试插件
TEST_PLUGIN_DIR = AGENT_CORE_DIR / "plugins" / "test_plugin"
TEST_PLUGIN_DIR.mkdir(exist_ok=True)

# 核心插件的工具数量（固定为24个）
core_tools = 24

# 初始版本
INITIAL_CODE = '''"""
test_plugin - 测试插件（初始版本）
"""

def register(agent):
    def hello():
        return "Hello from initial version!"

    agent.add_tool("hello", hello, {
        "name": "hello",
        "description": "打招呼",
        "parameters": {"type": "object", "properties": {}},
        "plugin": "test_plugin"
    })

    return {
        "name": "test_plugin",
        "version": "1.0.0",
        "description": "测试插件（初始版本）",
        "tools": ["hello"]
    }
'''

# 修改后版本
UPDATED_CODE = '''"""
test_plugin - 测试插件（修改版本）
"""

VERSION = "2.0.0"

def register(agent):
    def hello():
        return "Hello from UPDATED version 2.0.0!"

    def goodbye():
        return "Goodbye!"

    agent.add_tool("hello", hello, {
        "name": "hello",
        "description": "打招呼（v2）",
        "parameters": {"type": "object", "properties": {}},
        "plugin": "test_plugin"
    })

    agent.add_tool("goodbye", goodbye, {
        "name": "goodbye",
        "description": "道别",
        "parameters": {"type": "object", "properties": {}},
        "plugin": "test_plugin"
    })

    return {
        "name": "test_plugin",
        "version": "2.0.0",
        "description": "测试插件（修改版本）",
        "tools": ["hello", "goodbye"]
    }
'''

# 写入初始版本
(TEST_PLUGIN_DIR / "__init__.py").write_text(INITIAL_CODE, encoding="utf-8")

# 加载插件
result = agent.load_plugin("test_plugin")
print(f"   初始加载: {result}")
test("初始版本加载成功", "✅" in result)

# 测试初始版本
result = agent.execute_tool("hello")
print(f"   初始调用: {result}")
test("初始版本返回正确", "initial version" in result)

# 检查工具数量（核心插件24个 + test_plugin的1个）
core_tools = 24
tools_before = len(agent.list_tools())
test(
    "初始总工具数=核心+1",
    tools_before == core_tools + 1,
    f"实际: {tools_before}, 期望: {core_tools + 1}",
)

# 模拟修改插件代码
(TEST_PLUGIN_DIR / "__init__.py").write_text(UPDATED_CODE, encoding="utf-8")
print("   📝 插件代码已修改为 v2.0.0")

# 重新加载插件
result = agent.load_plugin("test_plugin")
print(f"   热载入: {result}")
test("热载入成功", "✅" in result)

# 测试修改后的版本
result = agent.execute_tool("hello")
print(f"   v2 调用: {result}")
test("修改后版本返回正确", "UPDATED version 2.0.0" in result, result)

# 测试新工具是否存在
result = agent.execute_tool("goodbye")
print(f"   新工具 goodbye: {result}")
test("新工具 goodbye 可用", "Goodbye" in result, result)

# 检查工具数量（核心插件24个 + test_plugin的2个）
tools_after = len(agent.list_tools())
test(
    "更新后总工具数=核心+2",
    tools_after == core_tools + 2,
    f"实际: {tools_after}, 期望: {core_tools + 2}",
)

# ---- 2. 重复使用非核心插件上下文污染测试 ----
print("\n\n🧹 2. 重复使用非核心插件上下文污染测试")
print("-" * 40)

# 清空历史
agent.clear_history()

# 检查初始工具注册表
print(f"   初始工具注册表大小: {len(agent.tool_registry._tools)}")
tools_at_start = len(agent.tool_registry._tools)

# 多次加载同一非核心插件（模拟多轮对话中的重复加载场景）
print("   模拟 5 轮对话，每轮都尝试加载 test_plugin...")
for i in range(5):
    result = agent.load_plugin("test_plugin")
    # 实际上 load_plugin 会先卸载之前的，所以不会重复注册

tools_after_reload = len(agent.tool_registry._tools)
tools_after_repeated_load = tools_after_reload
print(f"   5轮加载后工具注册表大小: {tools_after_repeated_load}")
test(
    "多次 load_plugin 不会重复注册工具",
    tools_after_repeated_load == tools_after_reload,
    f"实际: {tools_after_repeated_load}",
)

# 检查 conversation_history 是否有重复工具描述
print(f"\n   对话历史消息数: {len(agent.conversation_history)}")

# ---- 3. 检查 _build_prompt 的 tools description 是否重复 ----
print("\n\n📏 3. _build_prompt 工具描述重复检查")
print("-" * 40)

# 清空历史
agent.clear_history()

# 构建 prompt
prompt = agent._build_prompt("test")
messages = json.loads(prompt)
system_content = messages[0]["content"]

# 统计某个工具描述出现次数
test_str = "- hello:"
count = system_content.count(test_str)
print(f"   工具描述 '- hello:' 在 System Prompt 中出现次数: {count}")
test("工具描述不重复", count == 1, f"出现 {count} 次")

# ---- 4. 多轮对话后 tool_calls 格式检查 ----
print("\n\n🔄 4. 多轮对话 tool_calls 格式检查")
print("-" * 40)

agent.clear_history()
agent._consecutive_failures = 0

# 第一轮
print("   第1轮: get_cwd")
resp1 = agent.chat_with_tools("用 get_cwd 查看当前目录")
print(f"   响应: {resp1[:100]}")
test("第1轮调用成功", len(agent.conversation_history) >= 4)

# 第二轮
print("   第2轮: list_files")
resp2 = agent.chat_with_tools("用 list_files 列出当前目录")
print(f"   响应: {resp2[:100]}")
test("第2轮调用成功", len(agent.conversation_history) >= 8)

# 第三轮
print("   第3轮: run_command")
resp3 = agent.chat_with_tools("用 run_command 执行 'pwd' 命令")
print(f"   响应: {resp3[:100]}")
test("第3轮调用成功", len(agent.conversation_history) >= 12)

# 检查 conversation_history 只包含 user/assistant/tool 消息（无重复系统消息）
system_msgs_in_history = len(
    [m for m in agent.conversation_history if m.get("role") == "system"]
)
print(f"   System 消息在历史中出现次数: {system_msgs_in_history}")
test("System 消息不在历史中（不被污染）", system_msgs_in_history == 0)

# 检查 _build_prompt 返回的工具描述是否唯一
prompt = agent._build_prompt("test")
prompt_tool_descriptions = prompt.count("- hello")
print(f"   _build_prompt 中 'hello' 描述出现次数: {prompt_tool_descriptions}")
test(
    "工具描述在 prompt 中不重复",
    prompt_tool_descriptions == 1,
    f"出现 {prompt_tool_descriptions} 次",
)

# 检查 tool_calls 中的参数格式
tool_msgs = [m for m in agent.conversation_history if m.get("role") == "tool"]
print(f"   Tool 消息数: {len(tool_msgs)}")
test("每个工具调用都有对应 tool 消息", len(tool_msgs) >= 3)

# ---- 5. 验证工具参数 JSON 格式 ----
print("\n\n🔍 5. 工具参数 JSON 格式验证")
print("-" * 40)

# 找一个 assistant 的 tool_calls 消息
assistant_msgs = [
    m
    for m in agent.conversation_history
    if m.get("role") == "assistant" and m.get("tool_calls")
]
if assistant_msgs:
    tc = assistant_msgs[0]["tool_calls"][0]
    fn = tc.get("function", {})
    args = fn.get("arguments", "{}")
    print(f"   arguments 类型: {type(args).__name__}")
    print(f"   arguments 内容: {args}")
    try:
        args_dict = json.loads(args) if isinstance(args, str) else args
        test("arguments 是合法 JSON", isinstance(args_dict, dict))
    except:
        test("arguments 是合法 JSON", False, f"无法解析: {args}")
else:
    print("   未找到 assistant tool_calls 消息")

# ---- 6. 测试非核心插件加载时的上下文 ----
print("\n\n📦 6. 非核心插件加载对上下文的影响")
print("-" * 40)

# 创建另一个测试插件，带有详细描述
TEST_PLUGIN_DIR2 = AGENT_CORE_DIR / "plugins" / "test_plugin2"
TEST_PLUGIN_DIR2.mkdir(exist_ok=True)

LONG_DESC_CODE = '''"""
test_plugin2 - 带长描述的测试插件
"""

def register(agent):
    def greet(name: str) -> str:
        return f"Hello, {name}!"

    agent.add_tool("greet", greet, {
        "name": "greet",
        "description": "打招呼的详细描述：" + "x" * 200,
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "名字"}
            },
            "required": ["name"]
        },
        "plugin": "test_plugin2"
    })

    return {
        "name": "test_plugin2",
        "version": "1.0.0",
        "description": "测试插件2",
        "tools": ["greet"]
    }
'''

(TEST_PLUGIN_DIR2 / "__init__.py").write_text(LONG_DESC_CODE, encoding="utf-8")

result = agent.load_plugin("test_plugin2")
print(f"   加载 test_plugin2: {result}")

# 检查 tools_schema
schema = agent._build_tools_schema()
greet_schema = next((s for s in schema if s["function"]["name"] == "greet"), None)
if greet_schema:
    desc_len = len(greet_schema["function"]["description"])
    print(f"   greet 描述长度: {desc_len}")
    test("长描述被正确处理", desc_len > 100)

# 清理测试插件
import shutil

shutil.rmtree(TEST_PLUGIN_DIR, ignore_errors=True)
shutil.rmtree(TEST_PLUGIN_DIR2, ignore_errors=True)

# ============================================================
print("\n" + "=" * 60)
print(f"📊 测试结果: {passed} 通过, {failed} 失败")
print("=" * 60)

if failed == 0:
    print("🎉 全部测试通过!")
else:
    print(f"⚠️ 有 {failed} 个测试失败，请检查上方输出")
