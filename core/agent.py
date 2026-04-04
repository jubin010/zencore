# -*- coding: utf-8 -*-
"""
AgentCore - AI智能体核心
完全插件化架构，AI可插拔到任意外壳驱动
"""

import os
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

# 核心插件 — 永久保留，不会被卸载
CORE_PLUGINS = {
    "plugin_builder",
    "watcher_plugin",
    "memory_plugin",
    "env_plugin",
    "role_plugin",
}


class DriverInterface:
    """外壳驱动接口 - 所有外壳必须实现此接口"""

    def send_message(self, content: str):
        """发送消息"""
        raise NotImplementedError

    def send_image(self, path: str):
        """发送图片"""
        raise NotImplementedError

    def send_file(self, path: str):
        """发送文件"""
        raise NotImplementedError

    def get_input(self, prompt: str = "") -> str:
        """获取输入"""
        raise NotImplementedError

    def show_loading(self, message: str):
        """显示加载提示"""
        raise NotImplementedError

    def toast(self, message: str):
        """显示提示"""
        raise NotImplementedError

    def call_llm(self, messages: list) -> str:
        """
        调用 LLM — 由外壳驱动实现
        外壳决定连接哪个 LLM、用什么模型
        """
        raise NotImplementedError


class ToolRegistry:
    """工具注册表 - 管理所有可用工具"""

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        func: Callable,
        description: str = "",
        parameters: Dict = None,
        **kwargs,
    ):
        """注册工具"""
        self._tools[name] = {
            "func": func,
            "description": description,
            "parameters": parameters or {},
            **kwargs,
        }

    def unregister(self, name: str):
        """注销工具"""
        self._tools.pop(name, None)

    def get(self, name: str) -> Optional[Callable]:
        """获取工具函数"""
        tool = self._tools.get(name)
        return tool["func"] if tool else None

    def list_all(self) -> Dict[str, Dict]:
        """列出所有工具"""
        return self._tools.copy()

    def has(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self._tools


class AgentCore:
    """
    AI智能体核心类

    设计原则:
    1. 一切皆为插件 - 所有能力通过插件扩展
    2. AI可插拔 - 核心与外壳完全解耦
    3. 懒加载 - 按需加载插件，不一次性加载所有功能
    """

    _global_instance = None  # 全局实例引用

    def __init__(self, driver: DriverInterface = None, config: Dict = None):
        """
        初始化AI智能体核心

        Args:
            driver: 外壳驱动实例
            config: 配置字典
        """
        self.driver = driver
        self.config = config or {}
        self.tool_registry = ToolRegistry()

        # 上下文
        self.conversation_history = []
        self.max_history = self.config.get("max_history", 50)

        # 当前加载的非核心插件（用于自动卸载）
        self._loaded_plugins: set = set()

        # 角色与记忆
        self._current_role: str = ""
        self._current_memory_file: str = str(
            PLUGINS_DIR / "memory_plugin" / "memory.md"
        )

        # 加载核心插件
        self._load_core_plugins()

        # 设置全局引用
        AgentCore._global_instance = self

    def _load_core_plugins(self):
        """加载核心插件"""
        try:
            sys.path.insert(0, str(AGENT_CORE_DIR))
            from plugins import plugin_builder

            tools_info = plugin_builder.register(self)
            print(
                f"✅ 核心插件已加载: plugin_builder ({len(tools_info.get('tools', []))} 个工具)"
            )
        except Exception as e:
            print(f"⚠️ 核心插件加载失败: {e}")

        try:
            sys.path.insert(0, str(AGENT_CORE_DIR))
            from plugins import watcher_plugin

            tools_info = watcher_plugin.register(self)
            print(
                f"✅ 核心插件已加载: watcher_plugin ({len(tools_info.get('tools', []))} 个工具)"
            )
        except Exception as e:
            print(f"⚠️ 核心插件加载失败: {e}")

        try:
            sys.path.insert(0, str(AGENT_CORE_DIR))
            from plugins import memory_plugin

            tools_info = memory_plugin.register(self)
            print(
                f"✅ 核心插件已加载: memory_plugin ({len(tools_info.get('tools', []))} 个工具)"
            )
        except Exception as e:
            print(f"⚠️ 核心插件加载失败: {e}")

        try:
            sys.path.insert(0, str(AGENT_CORE_DIR))
            from plugins import env_plugin

            tools_info = env_plugin.register(self)
            print(
                f"✅ 核心插件已加载: env_plugin ({len(tools_info.get('tools', []))} 个工具)"
            )
        except Exception as e:
            print(f"⚠️ 核心插件加载失败: {e}")

        try:
            sys.path.insert(0, str(AGENT_CORE_DIR))
            from plugins import role_plugin

            tools_info = role_plugin.register(self)
            print(
                f"✅ 核心插件已加载: role_plugin ({len(tools_info.get('tools', []))} 个工具)"
            )
        except Exception as e:
            print(f"⚠️ 核心插件加载失败: {e}")

    def _get_plugin_tool_names(self, plugin_name: str) -> list:
        """获取属于指定插件的所有工具名"""
        return [
            name
            for name, info in self.tool_registry.list_all().items()
            if info.get("plugin") == plugin_name
        ]

    def _remove_plugin_tools(self, plugin_name: str) -> list:
        """清理指定插件的所有旧工具，返回被清理的工具列表"""
        old_tools = self._get_plugin_tool_names(plugin_name)
        for name in old_tools:
            self.tool_registry.unregister(name)
        return old_tools

    def unload_plugin(self, plugin_name: str) -> str:
        """
        卸载指定插件的所有工具

        核心插件不可卸载，会返回错误提示
        """
        if plugin_name in CORE_PLUGINS:
            return f"❌ 核心插件 {plugin_name} 不可卸载"

        old_tools = self._remove_plugin_tools(plugin_name)
        if old_tools:
            self._loaded_plugins.discard(plugin_name)
            if plugin_name in sys.modules:
                del sys.modules[f"plugins.{plugin_name}"]
            return f"✅ 已卸载 {plugin_name}（移除了 {len(old_tools)} 个工具）"
        return f"⚠️ 插件 {plugin_name} 未加载，无需卸载"

    def load_plugin(self, plugin_name: str) -> str:
        """
        从子目录加载/重载插件

        设计原则:
        1. 核心插件永久保留，不会被卸载
        2. 加载新插件时自动卸载上一个非核心插件（保持注册表精简）
        3. 先清理旧工具，再注册新工具 — 确保修改完全生效
        4. 失败时返回明确错误信息 — AI 可据此修复
        5. 不恢复旧模块 — AI 主动改代码，旧代码无意义

        Args:
            plugin_name: 插件目录名（如 'weather_plugin'）

        Returns:
            加载结果描述
        """
        plugin_dir = PLUGINS_DIR / plugin_name
        if not plugin_dir.is_dir():
            return f"❌ 插件目录不存在: {plugin_name}"

        init_file = plugin_dir / "__init__.py"
        if not init_file.exists():
            return f"❌ 插件缺少 __init__.py: {plugin_name}"

        # 自动卸载上一个非核心插件（保持注册表精简）
        unloaded_msg = ""
        if plugin_name not in CORE_PLUGINS and plugin_name not in self._loaded_plugins:
            for prev in list(self._loaded_plugins):
                if prev != plugin_name:
                    self.unload_plugin(prev)
                    unloaded_msg = f"（已自动卸载 {prev}）"
                    break

        # 清理该插件的旧工具
        old_tools = self._remove_plugin_tools(plugin_name)

        # 清除模块缓存，强制从磁盘重新加载
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
            if old_tools:
                removed = [t for t in old_tools if t not in new_tools]
                if removed:
                    msg += f", 已移除旧工具: {', '.join(removed)}"
            return msg
        except Exception as e:
            return f"❌ 注册失败: {e}"

    def reload_plugins(self) -> str:
        """重新加载所有插件"""
        results = []
        for plugin_dir in sorted(PLUGINS_DIR.iterdir()):
            if plugin_dir.is_dir() and (plugin_dir / "__init__.py").exists():
                if plugin_dir.name not in ("__pycache__",):
                    result = self.load_plugin(plugin_dir.name)
                    results.append(result)
        return "\n".join(results)

    # ==================== 工具管理 ====================

    def add_tool(
        self,
        name: str,
        func: Callable,
        description: str = "",
        parameters: Dict = None,
        **kwargs,
    ):
        """
        注册工具

        Args:
            name: 工具名
            func: 工具函数
            description: 工具描述（字符串或包含 name/description/parameters/plugin 等字段的字典）
            parameters: 参数 schema
            **kwargs: 额外元数据（如 plugin="xxx"）
        """
        if isinstance(description, dict):
            desc_str = description.get("description", "")
            params = description.get("parameters")
            extra = {
                k: v
                for k, v in description.items()
                if k not in ("name", "description", "parameters")
            }
            extra.update(kwargs)
            self.tool_registry.register(
                name, func, desc_str, params or parameters, **extra
            )
        else:
            self.tool_registry.register(name, func, description, parameters, **kwargs)

    def remove_tool(self, name: str):
        """移除工具"""
        self.tool_registry.unregister(name)

    def list_tools(self) -> Dict[str, Dict]:
        """列出所有工具"""
        return self.tool_registry.list_all()

    def execute_tool(self, name: str, **kwargs) -> str:
        """执行工具"""
        func = self.tool_registry.get(name)
        if func:
            try:
                return func(**kwargs)
            except Exception as e:
                return f"❌ 工具执行失败: {str(e)}\n{traceback.format_exc()}"
        else:
            return f"❌ 未知工具: {name}"

    # ==================== 对话管理 ====================

    def add_message(self, role: str, content: str):
        """添加对话消息"""
        self.conversation_history.append(
            {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        )
        # 限制历史长度
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history :]

    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []

    # ==================== LLM交互 ====================

    def _build_prompt(self, user_message: str) -> str:
        """构建发送给LLM的提示词"""

        # 获取可用工具描述
        tools_desc = self._get_tools_description()

        # 读取插件注册表作为AI的自我认知
        plugins_info = self._get_plugins_info()

        system_prompt = f"""你是一个AI智能体，你的核心能力由插件提供。

## 你的身份

一切皆为插件。你的所有能力都来自插件，你也可以创造新的插件。
"""

        if self._current_role:
            system_prompt += f"\n## 你的角色\n\n{self._current_role}\n"

        system_prompt += f"""
## 当前已加载的工具

{tools_desc}

## 插件索引

{plugins_info}

## 你的记忆

你的记忆存放在 `{self._current_memory_file}` 中。
使用 `read_file` 读取记忆，使用 `write_file` 或 `append_file` 更新记忆。
记忆由你自主维护，格式为纯 Markdown。

## 工作原则

1. **按需加载**: 需要什么功能，就用 `load_plugin` 加载对应插件
2. **自我进化**: 遇到没有的工具，用 `write_plugin` 编写新插件
3. **用完即走**: 不需要的插件用 `unload_plugin` 卸载，保持精简
4. **工具优先**: 优先使用工具解决问题，不要凭空编造
5. **自主探索**: 用环境工具感知世界，用记忆工具记录发现
6. **上下文管理**: 话题结束后，先 `write_memory` 归档结论，再 `clear_history` 清空圆桌

## 角色能力

你拥有角色决策权。你可以：
- 用 `list_roles` 查看可用角色
- 用 `switch_role` 切换身份和记忆
- 用 `create_role` 创造全新角色，定义身份、插件清单和记忆
- 切换角色后，用 `load_plugin` 自主加载角色所需的插件
- 根据用户需求，自主决定是否需要切换或创造新角色

## 上下文管理

圆桌会议（对话历史）是你的短期记忆。当它变得太长时：
1. 切换到 **秘书** 角色
2. 回顾讨论，提取核心结论
3. 用 `write_memory` 或 `append_file` 将摘要写入记忆
4. 用 `clear_history` 清空圆桌，恢复清净

## 响应格式

当需要执行工具时，返回JSON格式:
{{"tool": "工具名", "params": {{"参数名": "参数值"}}}}

当直接回答时，直接返回文字内容。

## 当前时间
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

        # 构建消息列表
        messages = [
            {"role": "system", "content": system_prompt},
            *self.conversation_history,
            {"role": "user", "content": user_message},
        ]

        return json.dumps(messages, ensure_ascii=False)

    def _get_tools_description(self) -> str:
        """获取工具描述"""
        tools = self.tool_registry.list_all()
        if not tools:
            return "(暂无已加载工具)"

        lines = []
        for name, info in tools.items():
            desc = info.get("description", "无描述")
            lines.append(f"- {name}: {desc}")
        return "\n".join(lines)

    def _get_plugins_info(self) -> str:
        """读取插件注册表"""
        if PLUGINS_MD.exists():
            try:
                with open(PLUGINS_MD, "r", encoding="utf-8") as f:
                    return f.read()
            except:
                pass
        return "(插件注册表不存在)"

    def chat(self, message: str) -> str:
        """同步对话 - 完整的对话处理"""
        self.add_message("user", message)

        # 构建提示词
        prompt = self._build_prompt(message)

        # 调用LLM
        response = self._call_llm(prompt)

        self.add_message("assistant", response)

        return response

    def chat_with_tools(self, message: str) -> str:
        """
        带工具调用的对话
        支持多轮工具调用直到LLM返回最终答案
        """
        self.add_message("user", message)

        # 构建初始提示词
        prompt = self._build_prompt(message)

        # 多轮对话循环
        max_turns = 10
        turns = 0

        while turns < max_turns:
            turns += 1

            # 调用LLM
            llm_response = self._call_llm(prompt)

            # 检查是否需要工具调用
            tool_call = self._extract_tool_call(llm_response)

            if tool_call is None:
                # 没有工具调用，返回结果
                self.add_message("assistant", llm_response)
                return llm_response

            # 执行工具
            tool_name = tool_call.get("tool")
            tool_params = tool_call.get("params", {})

            # 执行并获取结果
            tool_result = self.execute_tool(tool_name, **tool_params)

            # 将工具调用和结果添加到上下文
            tool_message = json.dumps(
                {"tool": tool_name, "params": tool_params, "result": tool_result},
                ensure_ascii=False,
            )

            self.add_message("assistant", f"[工具调用]\n{tool_message}")
            self.add_message("tool", tool_result)

            # 更新提示词继续对话
            prompt = self._build_prompt("")

        return "❌ 对话超时，已达到最大轮次限制"

    def _call_llm(self, prompt: str) -> str:
        """调用LLM — 委托给外壳驱动"""
        if self.driver and hasattr(self.driver, "call_llm"):
            try:
                messages = json.loads(prompt)
                return self.driver.call_llm(messages)
            except Exception as e:
                return f"❌ LLM调用失败: {str(e)}\n{traceback.format_exc()}"
        else:
            return "❌ 外壳驱动未实现 call_llm 方法"

    def _extract_tool_call(self, response: str) -> Optional[Dict]:
        """从LLM响应中提取工具调用"""
        # 尝试解析JSON
        try:
            # 查找JSON块
            match = re.search(r'\{[^{}]*"tool"[^{}]*\}', response)
            if match:
                return json.loads(match.group())
        except:
            pass

        return None

    # ==================== 便捷方法 ====================

    def send(self, content: str):
        """发送消息"""
        if self.driver:
            self.driver.send_message(content)
        else:
            print(content)

    def run_cli(self):
        """运行CLI交互模式"""
        print("=" * 50)
        print("🤖 AgentCore CLI 模式")
        print("=" * 50)
        print("输入消息与AI对话，输入 'quit' 退出")
        print("输入 'tools' 查看可用工具")
        print("输入 'clear' 清空对话历史")
        print("=" * 50)

        while True:
            try:
                user_input = input("\n👤 你: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ("quit", "exit", "退出"):
                    print("👋 再见!")
                    break

                if user_input.lower() == "tools":
                    tools = self.list_tools()
                    print(f"\n🛠️ 可用工具 ({len(tools)}个):")
                    for name, info in sorted(tools.items()):
                        print(f"   • {name}")
                    continue

                if user_input.lower() == "clear":
                    self.clear_history()
                    print("✅ 对话历史已清空")
                    continue

                # 对话
                print("\n🤖 AI: ", end="", flush=True)
                response = self.chat_with_tools(user_input)
                print(response)

            except KeyboardInterrupt:
                print("\n👋 再见!")
                break
            except Exception as e:
                print(f"\n❌ 错误: {str(e)}")

    def run_web(self, host: str = "0.0.0.0", port: int = 8080):
        """运行Web交互模式"""
        from drivers.web_driver import WebDriver

        driver = WebDriver(self)
        driver.run(host, port)


# ==================== 插件基类 ====================


class PluginBase:
    """插件基类（推荐使用）"""

    name = "BasePlugin"
    description = "基础插件"

    @classmethod
    def tool_info(cls):
        return {"name": cls.name, "description": cls.description, "tools": []}

    @classmethod
    def execute(cls, tool_name: str, **kwargs):
        raise NotImplementedError
