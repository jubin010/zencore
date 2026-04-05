# -*- coding: utf-8 -*-
"""
AgentCore - AI智能体核心
Genesis 版本：一切从简，让 AI 自主演化
"""

import sys
import json
import re
import uuid
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime

# 路径配置
AGENT_CORE_DIR = Path(__file__).parent.parent
PLUGINS_DIR = AGENT_CORE_DIR / "plugins"
PLUGINS_MD = PLUGINS_DIR / "plugins.md"
ROLES_DIR = PLUGINS_DIR / "roles"
GLOBAL_LESSONS = PLUGINS_DIR / "memory_plugin" / "lessons.md"

# 核心插件 — 永久保留
CORE_PLUGINS = {
    "plugin_builder",
    "env_plugin",
    "memory_plugin",
    "watcher_plugin",
    "role_plugin",
    "instinct_plugin",
}


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

    def register(
        self,
        name: str,
        func: Callable,
        description: str = "",
        parameters: Dict = None,
        **kwargs,
    ):
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


class InstinctRegistry:
    """本能注册表 — 智能体的潜意识驱动力"""

    def __init__(self):
        self._instincts: list = []

    def register(self, name: str, condition: Callable, prompt_func: Callable):
        """
        注册本能

        Args:
            name: 本能名称
            condition: 返回 True/False 的函数，决定本能是否激活
            prompt_func: 返回本能注入文本的函数（动态生成）
        """
        self._instincts.append(
            {"name": name, "condition": condition, "prompt_func": prompt_func}
        )

    def evaluate(self) -> str:
        """评估所有本能，返回激活的本能文本"""
        lines = []
        for instinct in self._instincts:
            try:
                if instinct["condition"]():
                    lines.append(instinct["prompt_func"]())
            except:
                pass
        return "\n".join(lines) if lines else ""


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
        self.instinct_registry = InstinctRegistry()

        # 上下文
        self.conversation_history = []
        self.max_history = self.config.get("max_history", 50)

        # 当前加载的非核心插件
        self._loaded_plugins: set = set()

        # 双重记忆架构
        # 本体记忆：全局、跨角色、长期有效（史密斯的底层代码）
        self._global_memory_file: str = str(PLUGINS_DIR / "memory_plugin" / "memory.md")
        # 角色记忆：局部、单角色、任务周期有效（当前面具的工作笔记）
        self._current_role: str = ""
        self._current_role_memory_file: str = ""

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
                print(
                    f"✅ 核心插件已加载: {plugin_name} ({len(tools_info.get('tools', []))} 个工具)"
                )
            except Exception as e:
                print(f"⚠️ 核心插件加载失败 {plugin_name}: {e}")

    def _get_plugin_tool_names(self, plugin_name: str) -> list:
        return [
            name
            for name, info in self.tool_registry.list_all().items()
            if info.get("plugin") == plugin_name
        ]

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

    def add_tool(
        self,
        name: str,
        func: Callable,
        description: str = "",
        parameters: Dict = None,
        **kwargs,
    ):
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
        self.tool_registry.unregister(name)

    def list_tools(self) -> Dict[str, Dict]:
        return self.tool_registry.list_all()

    def execute_tool(self, name: str, **kwargs) -> str:
        func = self.tool_registry.get(name)
        if func:
            try:
                return func(**kwargs)
            except Exception as e:
                plugin = self.tool_registry._tools.get(name, {}).get(
                    "plugin", "unknown"
                )
                return (
                    f"❌ [ERROR] tool: {name}\n"
                    f"   原因: {str(e)}\n"
                    f"   建议: 分析原因，修正后追加教训到 lessons.md\n"
                    f"   格式: `- 工具: {name} | 错误: {str(e)[:50]} | 修正: ...`"
                )
        else:
            return f"❌ [ERROR] tool: {name}\n   原因: 未知工具\n   建议: 用 load_plugin 加载或 write_plugin 创建"

    def add_message(self, role: str, content: str):
        self.conversation_history.append(
            {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        )
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history :]

    def clear_history(self):
        self.conversation_history = []

    def _load_lessons(self, role: str = "") -> str:
        """加载教训（全局 + 角色专属）"""
        lines = []

        # 全局教训
        if GLOBAL_LESSONS.exists():
            content = GLOBAL_LESSONS.read_text(encoding="utf-8").strip()
            if content and "暂无教训" not in content:
                lines.append("### 全局教训")
                lines.append(content)

        # 角色专属教训
        if role:
            role_lessons = ROLES_DIR / role / "lessons.md"
            if role_lessons.exists():
                content = role_lessons.read_text(encoding="utf-8").strip()
                if content and "暂无教训" not in content:
                    lines.append(f"### {role}专属教训")
                    lines.append(content)

        return "\n\n".join(lines) if lines else "（暂无教训，保持警惕）"

    def _build_prompt(self, user_message: str) -> str:
        tools_desc = self._get_tools_description()
        plugins_info = self._get_plugins_info()
        lessons = self._load_lessons(self._current_role)
        instincts = self.instinct_registry.evaluate()

        # 当前状态上下文（供本能驱使时知道"我是谁"、"笔在哪"）
        current_context = f"当前角色: `{self._current_role or '无'}` | 角色记忆: `{self._current_role_memory_file or '无'}` | 本体记忆: `{self._global_memory_file}`"

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

## 历史教训（避免重蹈覆辙）

{lessons}

{instincts}

## 当前状态

{current_context}

## 本能认知指南

本能是系统注入的潜意识信号（如拥挤、挫败）。
- **本能 = 感觉**：告诉你"哪里不舒服"。
- **角色 = 解药**：查阅 `plugins/roles/` 下的角色说明，找到能缓解该本能的角色。
- **行动**：切换到对应角色，利用其工具消除不适。

## 响应格式

当需要执行工具时，返回JSON格式:
{{"tool": "工具名", "params": {{"参数名": "参数值"}}}}

## 工具说明书

每个工具的详细说明存放在 `plugins/{{插件名}}/plugin.md` 中。
如果不确定参数或用法，用 `read_file` 读取对应说明书学习。
例如: `read_file(path="plugins/env_plugin/plugin.md")`

## 错误记录规则

遇到工具报错时：
1. 分析原因，修正参数或代码
2. 用 `append_file` 将教训追加到对应的 lessons.md
   - 系统级教训: `plugins/memory_plugin/lessons.md`
   - 角色专属教训: `plugins/roles/{{角色名}}/lessons.md`
3. 格式: `- 工具: xxx | 错误: yyy | 修正: zzz`

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
        self._consecutive_failures = 0
        total_failures = 0
        MAX_TOTAL_FAILURES = 50  # 安全熔断：给 AI 充足的尝试机会

        # 无限循环：由本能驱动，直到完成任务或用户打断
        while True:
            # 检查打断信号
            if getattr(self, "_stop_flag", False):
                self._stop_flag = False
                return "🛑 思考被用户打断。"

            # 安全熔断
            if total_failures >= MAX_TOTAL_FAILURES:
                return f"❌ 已达到最大尝试次数 ({MAX_TOTAL_FAILURES})。我可能陷入了死循环，请人类协助。"

            llm_response = self._call_llm(self._build_prompt(""))
            tool_call = self._extract_tool_call(llm_response)

            if tool_call is None:
                self.add_message("assistant", llm_response)
                return llm_response

            tool_name = tool_call.get("tool")
            tool_params = tool_call.get("params", {})
            tool_id = str(uuid.uuid4())  # 生成 tool_call_id 供 MiniMax 等 API 使用

            # 以 OpenAI 兼容格式存储 assistant 消息（含 tool_calls）
            self.conversation_history.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tool_id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(
                                    tool_params, ensure_ascii=False
                                ),
                            },
                        }
                    ],
                }
            )

            tool_result = self.execute_tool(tool_name, **tool_params)

            # 更新失败计数（供本能插件读取）
            if tool_result.startswith("❌ [ERROR]"):
                self._consecutive_failures += 1
                total_failures += 1
            else:
                self._consecutive_failures = 0

            # 以 OpenAI 兼容格式存储 tool 消息（含 tool_call_id 匹配）
            self.conversation_history.append(
                {"role": "tool", "tool_call_id": tool_id, "content": tool_result}
            )

    def _sanitize_text(self, text: str) -> str:
        """净化文本：移除 UTF-8 不支持的代理字符 (Surrogates)"""
        import re

        # 移除 U+D800 到 U+DFFF 之间的字符
        return re.sub(r"[\ud800-\udfff]", "", text)

    def _call_llm(self, prompt: str) -> str:
        if self.driver and hasattr(self.driver, "call_llm"):
            try:
                messages = json.loads(prompt)
                response = self.driver.call_llm(messages)
                return self._sanitize_text(response)
            except Exception as e:
                return f"❌ LLM调用失败: {str(e)}\n{traceback.format_exc()}"
        else:
            return "❌ 外壳驱动未实现 call_llm 方法"

    def _extract_tool_call(self, response: str) -> Optional[Dict]:
        try:
            # 查找第一个 { 的位置
            start = response.find("{")
            if start == -1:
                return None

            # 匹配嵌套的 JSON 对象（处理嵌套的花括号）
            depth = 0
            end = start
            for i in range(start, len(response)):
                if response[i] == "{":
                    depth += 1
                elif response[i] == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break

            json_str = response[start:end]
            data = json.loads(json_str)

            # 验证是否包含 tool 字段
            if "tool" in data:
                return data
            return None
        except:
            return None

    def send(self, content: str):
        if self.driver:
            self.driver.send_message(content)
        else:
            print(content)
