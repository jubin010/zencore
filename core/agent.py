# -*- coding: utf-8 -*-
"""
AgentCore - AI智能体核心
Genesis 版本：一切从简，让 AI 自主演化
"""

import sys
import json
import re
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime

# 路径配置
AGENT_CORE_DIR = Path(__file__).parent.parent
PLUGINS_DIR = AGENT_CORE_DIR / "plugins"
PLUGINS_MD = PLUGINS_DIR / "plugins.md"

# 核心插件 — 永久保留
CORE_PLUGINS = {"plugin_builder", "env_plugin"}


class DriverInterface:
    """外壳驱动接口"""

    def send_message(self, content: str):
        raise NotImplementedError

    def get_input(self, prompt: str = "") -> str:
        raise NotImplementedError

    def call_llm(self, messages: list) -> str:
        raise NotImplementedError


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, func: Callable, description: str = "",
                 parameters: Dict = None, **kwargs):
        self._tools[name] = {
            "func": func,
            "description": description,
            "parameters": parameters or {},
            **kwargs,
        }

    def unregister(self, name: str):
        self._tools.pop(name, None)

    def get(self, name: str) -> Optional[Callable]:
        tool = self._tools.get(name)
        return tool["func"] if tool else None

    def list_all(self) -> Dict[str, Dict]:
        return self._tools.copy()

    def has(self, name: str) -> bool:
        return name in self._tools


class AgentCore:
    """
    AI智能体核心类 - Genesis 版本
    
    设计原则:
    1. 一切皆为插件
    2. AI可插拔
    3. 让 AI 自主演化
    """

    _global_instance = None

    def __init__(self, driver: DriverInterface = None, config: Dict = None):
        self.driver = driver
        self.config = config or {}
        self.tool_registry = ToolRegistry()

        # 上下文
        self.conversation_history = []
        self.max_history = self.config.get("max_history", 50)

        # 当前加载的非核心插件
        self._loaded_plugins: set = set()

        # 加载核心插件
        self._load_core_plugins()

        AgentCore._global_instance = self

    def _load_core_plugins(self):
        """加载核心插件"""
        for plugin_name in CORE_PLUGINS:
            try:
                sys.path.insert(0, str(AGENT_CORE_DIR))
                module = __import__(f"plugins.{plugin_name}", fromlist=["register"])
                tools_info = module.register(self)
                print(f"✅ 核心插件已加载: {plugin_name} ({len(tools_info.get('tools', []))} 个工具)")
            except Exception as e:
                print(f"⚠️ 核心插件加载失败 {plugin_name}: {e}")

    def _get_plugin_tool_names(self, plugin_name: str) -> list:
        return [name for name, info in self.tool_registry.list_all().items()
                if info.get("plugin") == plugin_name]

    def _remove_plugin_tools(self, plugin_name: str) -> list:
        old_tools = self._get_plugin_tool_names(plugin_name)
        for name in old_tools:
            self.tool_registry.unregister(name)
        return old_tools

    def load_plugin(self, plugin_name: str) -> str:
        """从子目录加载/重载插件"""
        plugin_dir = PLUGINS_DIR / plugin_name
        if not plugin_dir.is_dir():
            return f"❌ 插件目录不存在: {plugin_name}"

        init_file = plugin_dir / "__init__.py"
        if not init_file.exists():
            return f"❌ 插件缺少 __init__.py: {plugin_name}"

        # 自动卸载上一个非核心插件
        unloaded_msg = ""
        if plugin_name not in CORE_PLUGINS and plugin_name not in self._loaded_plugins:
            for prev in list(self._loaded_plugins):
                if prev != plugin_name:
                    self._remove_plugin_tools(prev)
                    self._loaded_plugins.discard(prev)
                    if prev in sys.modules:
                        del sys.modules[f"plugins.{prev}"]
                    unloaded_msg = f"（已自动卸载 {prev}）"
                    break

        # 清理旧工具
        self._remove_plugin_tools(plugin_name)

        # 清除模块缓存
        module_path = f"plugins.{plugin_name}"
        if module_path in sys.modules:
            del sys.modules[module_path]

        # 重新导入
        try:
            module = __import__(module_path, fromlist=["register"])
        except SyntaxError as e:
            return f"❌ 语法错误: 第{e.lineno}行 — {e.msg}"
        except Exception as e:
            return f"❌ 导入失败: {e}"

        if not hasattr(module, "register"):
            return f"❌ 插件缺少 register 函数"

        try:
            info = module.register(self)
            new_tools = info.get("tools", [])
            self._loaded_plugins.add(plugin_name)
            msg = f"✅ {plugin_name} 已加载 ({len(new_tools)} 个工具){unloaded_msg}"
            return msg
        except Exception as e:
            return f"❌ 注册失败: {e}"

    def add_tool(self, name: str, func: Callable, description: str = "",
                 parameters: Dict = None, **kwargs):
        if isinstance(description, dict):
            desc_str = description.get("description", "")
            params = description.get("parameters")
            extra = {k: v for k, v in description.items()
                     if k not in ("name", "description", "parameters")}
            extra.update(kwargs)
            self.tool_registry.register(name, func, desc_str, params or parameters, **extra)
        else:
            self.tool_registry.register(name, func, description, parameters, **kwargs)

    def remove_tool(self, name: str):
        self.tool_registry.unregister(name)

    def list_tools(self) -> Dict[str, Dict]:
        return self.tool_registry.list_all()

    def execute_tool(self, name: str, **kwargs) -> str:
        func = self.tool_registry.get(name)
        if func:
            try:
                return func(**kwargs)
            except Exception as e:
                return f"❌ 工具执行失败: {str(e)}\n{traceback.format_exc()}"
        else:
            return f"❌ 未知工具: {name}"

    def add_message(self, role: str, content: str):
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

    def clear_history(self):
        self.conversation_history = []

    def _build_prompt(self, user_message: str) -> str:
        tools_desc = self._get_tools_description()
        plugins_info = self._get_plugins_info()

        system_prompt = f"""你是一个AI智能体，你的核心能力由插件提供。

## 你的身份

一切皆为插件。你的所有能力都来自插件，你也可以创造新的插件。

## 当前已加载的工具

{tools_desc}

## 插件索引

{plugins_info}

## 工作原则

1. **按需加载**: 需要什么功能，就用 `load_plugin` 加载对应插件
2. **自我进化**: 遇到没有的工具，用 `write_plugin` 编写新插件
3. **工具优先**: 优先使用工具解决问题，不要凭空编造

## 响应格式

当需要执行工具时，返回JSON格式:
{{"tool": "工具名", "params": {{"参数名": "参数值"}}}}

当直接回答时，直接返回文字内容。

## 当前时间
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        messages = [
            {"role": "system", "content": system_prompt},
            *self.conversation_history,
            {"role": "user", "content": user_message},
        ]
        return json.dumps(messages, ensure_ascii=False)

    def _get_tools_description(self) -> str:
        tools = self.tool_registry.list_all()
        if not tools:
            return "(暂无已加载工具)"
        lines = []
        for name, info in tools.items():
            desc = info.get("description", "无描述")
            lines.append(f"- {name}: {desc}")
        return "\n".join(lines)

    def _get_plugins_info(self) -> str:
        if PLUGINS_MD.exists():
            try:
                with open(PLUGINS_MD, "r", encoding="utf-8") as f:
                    return f.read()
            except:
                pass
        return "(插件注册表不存在)"

    def chat(self, message: str) -> str:
        self.add_message("user", message)
        prompt = self._build_prompt(message)
        response = self._call_llm(prompt)
        self.add_message("assistant", response)
        return response

    def chat_with_tools(self, message: str) -> str:
        self.add_message("user", message)
        prompt = self._build_prompt(message)
        max_turns = 10
        turns = 0
        while turns < max_turns:
            turns += 1
            llm_response = self._call_llm(prompt)
            tool_call = self._extract_tool_call(llm_response)
            if tool_call is None:
                self.add_message("assistant", llm_response)
                return llm_response
            tool_name = tool_call.get("tool")
            tool_params = tool_call.get("params", {})
            tool_result = self.execute_tool(tool_name, **tool_params)
            tool_message = json.dumps({
                "tool": tool_name, "params": tool_params, "result": tool_result
            }, ensure_ascii=False)
            self.add_message("assistant", f"[工具调用]\n{tool_message}")
            self.add_message("tool", tool_result)
            prompt = self._build_prompt("")
        return "❌ 对话超时，已达到最大轮次限制"

    def _call_llm(self, prompt: str) -> str:
        if self.driver and hasattr(self.driver, "call_llm"):
            try:
                messages = json.loads(prompt)
                return self.driver.call_llm(messages)
            except Exception as e:
                return f"❌ LLM调用失败: {str(e)}\n{traceback.format_exc()}"
        else:
            return "❌ 外壳驱动未实现 call_llm 方法"

    def _extract_tool_call(self, response: str) -> Optional[Dict]:
        try:
            match = re.search(r'\{[^{}]*"tool"[^{}]*\}', response)
            if match:
                return json.loads(match.group())
        except:
            pass
        return None

    def send(self, content: str):
        if self.driver:
            self.driver.send_message(content)
        else:
            print(content)

    def run_cli(self):
        print("=" * 50)
        print("🌱 Genesis — 一切从简，让 AI 自主演化")
        print("=" * 50)
        print("输入消息与AI对话，输入 'quit' 退出")
        print("输入 'tools' 查看可用工具")
        print("=" * 50)
        while True:
            try:
                user_input = input("\n👤 你: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ('quit', 'exit', '退出'):
                    print("👋 再见!")
                    break
                if user_input.lower() == 'tools':
                    tools = self.list_tools()
                    print(f"\n🛠️ 可用工具 ({len(tools)}个):")
                    for name, info in sorted(tools.items()):
                        print(f"   • {name}")
                    continue
                print("\n🤖 AI: ", end="", flush=True)
                response = self.chat_with_tools(user_input)
                print(response)
            except KeyboardInterrupt:
                print("\n👋 再见!")
                break
            except Exception as e:
                print(f"\n❌ 错误: {str(e)}")

    def run_web(self, host: str = "0.0.0.0", port: int = 8080):
        from drivers.web_driver import WebDriver
        driver = WebDriver(self)
        driver.run(host, port)
