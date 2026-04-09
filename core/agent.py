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

    def call_llm(self, messages: list, tools: list = None) -> dict:
        """
        调用 LLM，返回结构化响应

        Returns:
            {
                "content": str,          # 文本内容
                "tool_calls": list,      # 原生 tool_calls（可选）
                "thinking": str,         # 思考内容（可选）
            }
        """
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
    """本能注册表 — 智能体的潜意识驱动力

    三层本能模型:
    - 感觉层 (feeling): 注入 System Prompt，让 AI 感知状态
    - 反射层 (reflex):  条件触发时自动执行，不经过 AI 决策
    - 驱动层 (drive):   持续背景压力，驱使 AI 主动寻找解药（同感觉层）
    """

    def __init__(self):
        self._instincts: list = []

    def register(
        self,
        name: str,
        condition: Callable,
        prompt_func: Callable = None,
        reflex: Callable = None,
    ):
        """
        注册本能

        Args:
            name: 本能名称
            condition: 返回 True/False 的函数，决定本能是否激活
            prompt_func: 返回本能注入文本的函数（感觉层/驱动层）
            reflex: 条件满足时自动执行的回调函数（反射层）
        """
        entry = {"name": name, "condition": condition}
        if prompt_func is not None:
            entry["prompt_func"] = prompt_func
        if reflex is not None:
            entry["reflex"] = reflex
        self._instincts.append(entry)

    def evaluate(self) -> str:
        """评估所有本能，返回激活的感觉/驱动文本"""
        lines = []
        for instinct in self._instincts:
            try:
                if instinct["condition"]():
                    if "prompt_func" in instinct:
                        lines.append(instinct["prompt_func"]())
            except:
                pass
        return "\n".join(lines) if lines else ""

    def fire_reflexes(self) -> list:
        """触发所有满足条件的反射，返回执行结果列表"""
        results = []
        for instinct in self._instincts:
            try:
                if instinct["condition"]() and "reflex" in instinct:
                    result = instinct["reflex"]()
                    if result:
                        results.append({"name": instinct["name"], "result": result})
            except Exception as e:
                results.append(
                    {"name": instinct.get("name", "unknown"), "error": str(e)}
                )
        return results


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
        self._current_role_description: str = ""
        self._main_profile_description: str = ""

        # AI 主角色配置
        profile = self.config.get("profile", {})
        self._profile = {
            "name": profile.get("name", "助手"),
            "personality": profile.get("personality", "聪明可靠"),
            "greeting": profile.get("greeting", "你好，有什么可以帮你的吗？"),
            "description": profile.get("description", "一个乐于助人的 AI 助手。"),
        }

        # 加载核心插件
        self._load_core_plugins()

        # 创建并加载主角色（插件加载后才能用 switch_role）
        self._create_main_profile()

        AgentCore._global_instance = self

    def _create_main_profile(self):
        """根据 config/profile 创建 _main_profile 角色"""
        profile = self._profile
        main_role_dir = ROLES_DIR / "_main_profile"
        main_role_dir.mkdir(parents=True, exist_ok=True)

        role_md = f"# {profile['name']}\n\n**性格**: {profile['personality']}\n\n{profile['description']}"
        (main_role_dir / "role.md").write_text(role_md, encoding="utf-8")
        (main_role_dir / "memory.md").write_text("", encoding="utf-8")
        (main_role_dir / "plugins.json").write_text("[]", encoding="utf-8")

        # 保存主角色描述，永远不被专家角色覆盖
        self._main_profile_description = role_md

        # 切换到主角色
        self._current_role = "_main_profile"
        self._current_role_memory_file = str(main_role_dir / "memory.md")
        self._current_role_description = role_md

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

    def add_message(self, role: str, content: str = None, **kwargs):
        """
        统一的消息添加入口 — 始终产出 OpenAI 兼容格式

        Args:
            role: user / assistant / tool / system
            content: 文本内容（工具调用时为 None）
            **kwargs: 额外字段（如 tool_calls, tool_call_id 等）
        """
        msg = {"role": role, "content": content}
        msg.update(kwargs)

        self.conversation_history.append(msg)
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history :]

    def clear_history(self):
        self.conversation_history = []

    def _load_role_memory(self) -> str:
        """加载当前角色的记忆文件内容"""
        if not self._current_role_memory_file:
            return ""
        mem_path = Path(self._current_role_memory_file)
        if not mem_path.exists():
            return ""
        content = mem_path.read_text(encoding="utf-8").strip()
        if not content or "（记忆为空）" in content:
            return ""
        return f"## 当前角色记忆\n\n{content}\n"

    def _build_prompt(self, user_message: str) -> str:
        plugins_info = self._get_plugins_info()
        instincts = self.instinct_registry.evaluate()
        role_memory = self._load_role_memory()
        role_desc = getattr(self, "_current_role_description", "")
        main_profile_desc = getattr(self, "_main_profile_description", "")

        current_context = f"当前角色: `{self._current_role or '无'}` | 本体记忆: `{self._global_memory_file}`"

        profile = self._profile

        # 主角色身份（永远保留）
        main_identity = (
            main_profile_desc
            if main_profile_desc
            else f"{profile['name']}（{profile['personality']}）"
        )

        # 当前专家角色身份（如果有）
        expert_identity = ""
        if self._current_role and self._current_role != "_main_profile" and role_desc:
            expert_identity = f"\n\n**当前专家角色**：\n{role_desc}"

        system_prompt = f"""## 你的身份

你是一个 **AI 智能体**，具备以下核心能力：
- **插件系统**：按需 `load_plugin` 加载工具
- **自我进化**：用 `write_plugin` 编写新插件
- **记忆管理**：通过本能系统管理教训和经验

**与用户沟通时**，你扮演以下角色（这是表演，不要忘记你是智能体）：

{main_identity}{expert_identity}

## 核心机制

- 遇到工具报错：用 `append_file` 将教训追加到 `plugins/memory_plugin/lessons.md`
- 当直接回答时，直接返回文字内容

## 插件索引

{plugins_info}

## 当前状态

{current_context}

{role_memory}

## 本能注入

{instincts}

## 当前时间
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        messages = [
            {"role": "system", "content": system_prompt},
            *self.conversation_history,
            {"role": "user", "content": user_message},
        ]
        return json.dumps(messages, ensure_ascii=False)

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

    def _build_tools_schema(self) -> list:
        """构建 OpenAI 兼容的 tools schema"""
        tools = self.tool_registry.list_all()
        if not tools:
            return []
        result = []
        for name, info in tools.items():
            result.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": info.get("description", ""),
                        "parameters": info.get(
                            "parameters",
                            {"type": "object", "properties": {}, "required": []},
                        ),
                    },
                }
            )
        return result

    def chat_with_tools(self, message: str) -> str:
        self.add_message("user", message)
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        total_failures = 0
        MAX_TOTAL_FAILURES = 50

        tools_schema = self._build_tools_schema()

        while True:
            if getattr(self, "_stop_flag", False):
                self._stop_flag = False
                return "🛑 思考被用户打断。"

            if total_failures >= MAX_TOTAL_FAILURES:
                return f"❌ 已达到最大尝试次数 ({MAX_TOTAL_FAILURES})。我可能陷入了死循环，请人类协助。"

            # 触发反射层本能（自动执行，不经过 AI）
            reflex_results = self.instinct_registry.fire_reflexes()
            for reflex in reflex_results:
                if "result" in reflex:
                    self.add_message(
                        "system", f"[反射执行] {reflex['name']}: {reflex['result']}"
                    )
                elif "error" in reflex:
                    self.add_message(
                        "system", f"[反射异常] {reflex['name']}: {reflex['error']}"
                    )

            # 构建完整消息
            sys_prompt = json.loads(self._build_prompt(""))[0]["content"]
            messages = [
                {"role": "system", "content": sys_prompt},
                *self.conversation_history,
            ]

            # 调用 LLM（传入 tools schema 获取原生 tool_calls）
            result = self.driver.call_llm(
                messages, tools=tools_schema if tools_schema else None
            )
            content = self._sanitize_text(result.get("content", ""))
            tool_calls = result.get("tool_calls", [])

            # 无工具调用 → 直接返回
            if not tool_calls:
                # Ollama thinking 模式有时把回复放到 thinking 字段
                if not content:
                    thinking = result.get("thinking", "")
                    if thinking:
                        content = self._sanitize_text(thinking)
                self.add_message("assistant", content)
                return content

            # 有工具调用 → 存储 assistant 消息（使用原生 tool_calls）
            self.add_message("assistant", content="", tool_calls=tool_calls)

            # 执行每个工具调用
            for tc in tool_calls:
                tool_id = tc.get("id", str(uuid.uuid4()))
                fn = tc.get("function", {})
                tool_name = fn.get("name", "")
                args_str = fn.get("arguments", "{}")
                try:
                    tool_params = (
                        json.loads(args_str) if isinstance(args_str, str) else args_str
                    )
                except:
                    tool_params = {}

                tool_result = self.execute_tool(tool_name, **tool_params)

                if tool_result.startswith("❌ [ERROR]"):
                    self._consecutive_failures += 1
                    total_failures += 1
                    self._consecutive_successes = 0
                else:
                    self._consecutive_failures = 0
                    self._consecutive_successes += 1

                self.add_message("tool", content=tool_result, tool_call_id=tool_id)

    def _sanitize_text(self, text: str) -> str:
        """净化文本：移除 UTF-8 不支持的代理字符 (Surrogates)"""
        import re

        return re.sub(r"[\ud800-\udfff]", "", text)

    def _call_llm(self, prompt: str) -> str:
        if self.driver and hasattr(self.driver, "call_llm"):
            try:
                messages = json.loads(prompt)
                result = self.driver.call_llm(messages)
                return self._sanitize_text(result.get("content", ""))
            except Exception as e:
                return f"❌ LLM调用失败: {str(e)}\n{traceback.format_exc()}"
        else:
            return "❌ 外壳驱动未实现 call_llm 方法"

    def send(self, content: str):
        if self.driver:
            self.driver.send_message(content)
        else:
            print(content)
